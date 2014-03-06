# -*- coding: utf-8 -*-
import inspect
import warnings
from django.utils.datastructures import SortedDict
from django.db import models
from rest_framework.compat import get_concrete_model
from rest_framework.fields import Field
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import ModelSerializer, HyperlinkedModelSerializerOptions, _resolve_model
from drf_hal.fields import HalLinksField, HalEmbeddedField


class HalModelSerializer(ModelSerializer):
    """
    A subclass of ModelSerializer that follows the HAL specs (http://stateless.co/hal_specification.html).
    """
    _options_class = HyperlinkedModelSerializerOptions
    _default_view_name = '%(model_name)s-detail'
    _hyperlink_field_class = HyperlinkedRelatedField

    # Just a placeholder to ensure '_links' is the first field
    # The field itself is actually created on initialization,
    # when the view_name and lookup_field arguments are available.
    _links = Field()

    def __init__(self, *args, **kwargs):
        self.additional_links = {}

        super(HalModelSerializer, self).__init__(*args, **kwargs)

        if self.opts.view_name is None:
            self.opts.view_name = self._get_default_view_name(self.opts.model)

        _links = HalLinksField(
            view_name=self.opts.view_name,
            additional_links=self.additional_links,
            exclude=self.opts.exclude
        )
        _links.initialize(self, '_links')
        self.fields['_links'] = _links

    def _get_default_view_name(self, model):
        """
        Return the view name to use if 'view_name' is not specified in 'Meta'
        """
        model_meta = model._meta
        format_kwargs = {
            'app_label': model_meta.app_label,
            'model_name': model_meta.object_name.lower()
        }
        return self._default_view_name % format_kwargs

    def get_pk_field(self, model_field):
        if self.opts.fields and model_field.name in self.opts.fields:
            return self.get_field(model_field)

    def get_related_field(self, model_field, related_model, to_many):
        """
        Creates a default instance of a flat relational field.
        """
        # TODO: filter queryset using:
        # .using(db).complex_filter(self.rel.limit_choices_to)
        kwargs = {
            'queryset': related_model._default_manager,
            'view_name': self._get_default_view_name(related_model),
            'many': to_many
        }

        if model_field:
            kwargs['required'] = not(model_field.null or model_field.blank)

        if self.opts.lookup_field:
            kwargs['lookup_field'] = self.opts.lookup_field

        return self._hyperlink_field_class(**kwargs)

    def get_identity(self, data):
        """
        This hook is required for bulk update.
        We need to override the default, to use the _links as the identity.
        """
        try:
            return data.get('_links', None) and data['links'].get('self') and data['links']['self'].get('href')
        except AttributeError:
            return None

    def add_field_to_links(self, model_field, field):
        field.initialize(self, model_field.name)
        self.additional_links[model_field.name] = field

    def get_default_fields(self):
        """
        Return all the fields that should be serialized for the model.
        """

        cls = self.opts.model
        assert cls is not None, \
            "Serializer class '%s' is missing 'model' Meta option" % self.__class__.__name__
        opts = get_concrete_model(cls)._meta
        ret = SortedDict()
        nested = bool(self.opts.depth)

        # Deal with adding the primary key field
        pk_field = opts.pk
        while pk_field.rel and pk_field.rel.parent_link:
            # If model is a child via multitable inheritance, use parent's pk
            pk_field = pk_field.rel.to._meta.pk

        field = self.get_pk_field(pk_field)
        if field:
            ret[pk_field.name] = field

        # Deal with forward relationships
        forward_rels = [field for field in opts.fields if field.serialize]
        forward_rels += [field for field in opts.many_to_many if field.serialize]

        field = None
        for model_field in forward_rels:
            has_through_model = False

            if model_field.rel:
                to_many = isinstance(model_field,
                                     models.fields.related.ManyToManyField)
                related_model = _resolve_model(model_field.rel.to)

                if to_many and not model_field.rel.through._meta.auto_created:
                    has_through_model = True

            if model_field.rel and nested:
                if len(inspect.getargspec(self.get_nested_field).args) == 2:
                    warnings.warn(
                        'The `get_nested_field(model_field)` call signature '
                        'is due to be deprecated. '
                        'Use `get_nested_field(model_field, related_model, '
                        'to_many) instead',
                        PendingDeprecationWarning
                    )
                    field = self.get_nested_field(model_field)
                else:
                    field = self.get_nested_field(model_field, related_model, to_many)
            elif model_field.rel:
                if len(inspect.getargspec(self.get_nested_field).args) == 3:
                    warnings.warn(
                        'The `get_related_field(model_field, to_many)` call '
                        'signature is due to be deprecated. '
                        'Use `get_related_field(model_field, related_model, '
                        'to_many) instead',
                        PendingDeprecationWarning
                    )
                    self.add_field_to_links(model_field, self.get_related_field(model_field, to_many=to_many))
                else:
                    self.add_field_to_links(model_field, self.get_related_field(model_field, related_model, to_many))
            else:
                field = self.get_field(model_field)

            if field:
                if has_through_model:
                    field.read_only = True

                ret[model_field.name] = field

        # Deal with reverse relationships
        if not self.opts.fields:
            reverse_rels = []
        else:
            # Reverse relationships are only included if they are explicitly
            # present in the `fields` option on the serializer
            reverse_rels = opts.get_all_related_objects()
            reverse_rels += opts.get_all_related_many_to_many_objects()

        for relation in reverse_rels:
            accessor_name = relation.get_accessor_name()
            if not self.opts.fields or accessor_name not in self.opts.fields:
                continue
            related_model = relation.model
            to_many = relation.field.rel.multiple
            has_through_model = False
            is_m2m = isinstance(relation.field,
                                models.fields.related.ManyToManyField)

            if (is_m2m and
                    hasattr(relation.field.rel, 'through') and
                    not relation.field.rel.through._meta.auto_created):
                has_through_model = True

            if nested:
                field = self.get_nested_field(None, related_model, to_many)
            else:
                field = self.get_related_field(None, related_model, to_many)

            if field:
                if has_through_model:
                    field.read_only = True

                ret[accessor_name] = field

        # Add the `read_only` flag to any fields that have bee specified
        # in the `read_only_fields` option
        for field_name in self.opts.read_only_fields:
            assert field_name not in self.base_fields.keys(), (
                "field '%s' on serializer '%s' specified in "
                "`read_only_fields`, but also added "
                "as an explicit field.  Remove it from `read_only_fields`." %
                (field_name, self.__class__.__name__))
            assert field_name in ret, (
                "Non-existant field '%s' specified in `read_only_fields` "
                "on serializer '%s'." %
                (field_name, self.__class__.__name__))
            ret[field_name].read_only = True

        for field_name in self.opts.write_only_fields:
            assert field_name not in self.base_fields.keys(), (
                "field '%s' on serializer '%s' specified in "
                "`write_only_fields`, but also added "
                "as an explicit field.  Remove it from `write_only_fields`." %
                (field_name, self.__class__.__name__))
            assert field_name in ret, (
                "Non-existant field '%s' specified in `write_only_fields` "
                "on serializer '%s'." %
                (field_name, self.__class__.__name__))
            ret[field_name].write_only = True

        return ret

