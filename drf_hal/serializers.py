# -*- coding: utf-8 -*-
import copy
from django.utils.datastructures import SortedDict
from django.db import models
from rest_framework.compat import get_concrete_model
from rest_framework.fields import Field
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import ModelSerializer, HyperlinkedModelSerializerOptions, _resolve_model
from drf_hal.fields import HALLinksField, HALEmbeddedField


class HALModelSerializer(ModelSerializer):
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
        self.embedded_fields = {}

        super(HALModelSerializer, self).__init__(*args, **kwargs)

        if self.opts.view_name is None:
            self.opts.view_name = self._get_default_view_name(self.opts.model)

        _links = HALLinksField(
            view_name=self.opts.view_name,
            lookup_field=self.opts.lookup_field,
            additional_links=self.additional_links,
        )
        _links.initialize(self, '_links')
        self.fields['_links'] = _links

        if self.embedded_fields:
            _embedded = HALEmbeddedField(
                embedded_fields=self.embedded_fields,
            )
            _embedded.initialize(self, '_embedded')
            self.fields['_embedded'] = _embedded

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

        return self._hyperlink_field_class(**kwargs)

    def get_identity(self, data):
        """
        This hook is required for bulk update.
        We need to override the default, to use the _links as the identity.
        """
        try:
            return data.get('_links', None) and data['_links'].get('self') and data['_links']['self'].get('href')
        except AttributeError:
            return None

    def add_field_to_links(self, field_name, field):
        field.initialize(parent=self, field_name=field_name)
        self.additional_links[field_name] = field

    def add_field_to_embedded(self, field_name, field, has_through_model=False):
        field.initialize(parent=self, field_name=field_name)
        if has_through_model:
            field.read_only = True
        self.embedded_fields[field_name] = field

    def get_default_fields(self, base_fields):
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
                self.add_field_to_embedded(model_field.name, self.get_nested_field(model_field, related_model, to_many))
            elif model_field.rel and model_field.name in base_fields:
                key = model_field.name
                self.add_field_to_embedded(key, base_fields[key])
                base_fields.pop(key)
            elif model_field.rel:
                self.add_field_to_links(model_field.name, self.get_related_field(model_field, related_model, to_many))
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
                self.add_field_to_embedded(accessor_name, self.get_nested_field(None, related_model, to_many), has_through_model)
            else:
                self.add_field_to_embedded(accessor_name, self.get_related_field(None, related_model, to_many), has_through_model)

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

    def get_fields(self):
        """
        Returns the complete set of fields for the object as a dict.

        This will be the set of any explicitly declared fields,
        plus the set of fields returned by get_default_fields().
        """
        ret = SortedDict()

        # Get the explicitly declared fields
        base_fields = copy.deepcopy(self.base_fields)
        for key, field in base_fields.items():
            ret[key] = field

        # Add in the default fields
        default_fields = self.get_default_fields(ret)
        for key, val in default_fields.items():
            if key not in ret:
                ret[key] = val

        # If 'fields' is specified, use those fields, in that order.
        if self.opts.fields:
            assert isinstance(self.opts.fields, (list, tuple)), '`fields` must be a list or tuple'
            new = SortedDict()
            for key in self.opts.fields:
                new[key] = ret[key]
            ret = new

        # Remove anything in 'exclude'
        if self.opts.exclude:
            assert isinstance(self.opts.exclude, (list, tuple)), '`exclude` must be a list or tuple'
            for key in self.opts.exclude:
                ret.pop(key, None)
                self.additional_links.pop(key, None)
                self.embedded_fields.pop(key, None)

        for key, field in ret.items():
            field.initialize(parent=self, field_name=key)

        return ret

