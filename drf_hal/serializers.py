# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.db.models import FieldDoesNotExist
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import ModelSerializer, BaseSerializer
from rest_framework.fields import *
from rest_framework.utils import model_meta
from rest_framework.utils.field_mapping import get_field_kwargs, get_nested_relation_kwargs, get_relation_kwargs

from drf_hal.fields import HALLinksField, HALEmbeddedField


HALfields = ['_links', '_embedded']


class HALModelSerializer(ModelSerializer):
    """
    A subclass of ModelSerializer that follows the HAL specs (http://stateless.co/hal_specification.html).
    """
    _default_view_name = '%(model_name)s-detail'
    _related_class = HyperlinkedRelatedField

    def __init__(self, *args, **kwargs):
        self.additional_links = {}
        self.embedded_fields = {}
        super(HALModelSerializer, self).__init__(*args, **kwargs)

    def __save_related_field(self, instance, field_name, data):
        related_field = getattr(instance, field_name)
        if isinstance(data, dict):
            related_field.create(**data)
        else:
            related_field.add(data)

    def create(self, validated_attrs):
        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_attrs.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        to_many = {}
        related = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and field_name in validated_attrs:
                to_many[field_name] = validated_attrs.pop(field_name)

        instance = ModelClass.objects.create(**validated_attrs)

        for field_name, value in to_many.items():
            if isinstance(value, list):
                for item in value:
                    self.__save_related_field(instance, field_name, item)
            else:
                self.__save_related_field(instance, field_name, value)

        return instance

    def update(self, instance, validated_attrs):
        assert not any(
            isinstance(field, BaseSerializer) and not field.read_only
            for field in self.fields.values()
        ), (
            'The `.update()` method does not suport nested writable fields '
            'by default. Write an explicit `.update()` method for serializer '
            '`%s.%s`, or set `read_only=True` on nested serializer fields.' %
            (self.__class__.__module__, self.__class__.__name__)
        )

        for attr, value in validated_attrs.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

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

    def get_fields(self):
        declared_fields = copy.deepcopy(self._declared_fields)

        ret = OrderedDict()
        model = getattr(self.Meta, 'model')
        fields = getattr(self.Meta, 'fields', None)
        exclude = getattr(self.Meta, 'exclude', None)
        depth = getattr(self.Meta, 'depth', 0)
        extra_kwargs = getattr(self.Meta, 'extra_kwargs', {})

        assert not (fields and exclude), "Cannot set both 'fields' and 'exclude'."

        extra_kwargs = self._include_additional_options(extra_kwargs)

        # Retrieve metadata about fields & relationships on the model class.
        info = model_meta.get_field_info(model)

        # Use the default set of field names if none is supplied explicitly.
        if fields is None:
            fields = self._get_default_field_names(declared_fields, info)
            exclude = getattr(self.Meta, 'exclude', None)
            if exclude is not None:
                for field_name in exclude:
                    fields.remove(field_name)

        # Determine the set of model fields, and the fields that they map to.
        # We actually only need this to deal with the slightly awkward case
        # of supporting `unique_for_date`/`unique_for_month`/`unique_for_year`.
        model_field_mapping = {}
        for field_name in fields:
            if field_name in declared_fields:
                field = declared_fields[field_name]
                source = field.source or field_name
            else:
                try:
                    source = extra_kwargs[field_name]['source']
                except KeyError:
                    source = field_name
            # Model fields will always have a simple source mapping,
            # they can't be nested attribute lookups.
            if '.' not in source and source != '*':
                model_field_mapping[source] = field_name

        # Determine if we need any additional `HiddenField` or extra keyword
        # arguments to deal with `unique_for` dates that are required to
        # be in the input data in order to validate it.
        unique_fields = {}
        for model_field_name, field_name in model_field_mapping.items():
            try:
                model_field = model._meta.get_field(model_field_name)
            except FieldDoesNotExist:
                continue

            # Deal with each of the `unique_for_*` cases.
            for date_field_name in (
                    model_field.unique_for_date,
                    model_field.unique_for_month,
                    model_field.unique_for_year
            ):
                if date_field_name is None:
                    continue

                # Get the model field that is refered too.
                date_field = model._meta.get_field(date_field_name)

                if date_field.auto_now_add:
                    default = CreateOnlyDefault(timezone.now)
                elif date_field.auto_now:
                    default = timezone.now
                elif date_field.has_default():
                    default = model_field.default
                else:
                    default = empty

                if date_field_name in model_field_mapping:
                    # The corresponding date field is present in the serializer
                    if date_field_name not in extra_kwargs:
                        extra_kwargs[date_field_name] = {}
                    if default is empty:
                        if 'required' not in extra_kwargs[date_field_name]:
                            extra_kwargs[date_field_name]['required'] = True
                    else:
                        if 'default' not in extra_kwargs[date_field_name]:
                            extra_kwargs[date_field_name]['default'] = default
                else:
                    # The corresponding date field is not present in the,
                    # serializer. We have a default to use for the date, so
                    # add in a hidden field that populates it.
                    unique_fields[date_field_name] = HiddenField(default=default)

        # Now determine the fields that should be included on the serializer.
        for field_name in fields:
            is_links_field = False
            is_embedded_field = False

            if field_name in declared_fields:
                if info.relations:
                    field = declared_fields[field_name]
                    if not isinstance(field, HyperlinkedRelatedField):
                        self.embedded_fields[field_name] = field
                    else:
                        self.additional_links[field_name] = field
                if field_name in self.Meta.additional_links:
                    self.additional_links[field_name] = field
                else:
                    ret[field_name] = declared_fields[field_name]
                continue

            elif field_name in info.fields_and_pk:
                # Create regular model fields.
                model_field = info.fields_and_pk[field_name]
                field_cls = self._field_mapping[model_field]
                kwargs = get_field_kwargs(field_name, model_field)
                if 'choices' in kwargs:
                    # Fields with choices get coerced into `ChoiceField`
                    # instead of using their regular typed field.
                    field_cls = ChoiceField
                if not issubclass(field_cls, ModelField):
                    # `model_field` is only valid for the fallback case of
                    # `ModelField`, which is used when no other typed field
                    # matched to the model field.
                    kwargs.pop('model_field', None)
                if not issubclass(field_cls, CharField):
                    # `allow_blank` is only valid for textual fields.
                    kwargs.pop('allow_blank', None)

            elif field_name in info.relations:
                # Create forward and reverse relationships.
                relation_info = info.relations[field_name]
                if depth:
                    field_cls = self._get_nested_class(depth, relation_info)
                    kwargs = get_nested_relation_kwargs(relation_info)
                    is_embedded_field = True
                else:
                    field_cls = self._related_class
                    kwargs = get_relation_kwargs(field_name, relation_info)
                    # `view_name` is only valid for hyperlinked relationships.
                    if not issubclass(field_cls, HyperlinkedRelatedField):
                        kwargs.pop('view_name', None)
                    else:
                        is_links_field = True

            elif hasattr(model, field_name):
                # Create a read only field for model methods and properties.
                field_cls = ReadOnlyField
                kwargs = {}

            else:
                raise ImproperlyConfigured(
                    'Field name `%s` is not valid for model `%s`.' %
                    (field_name, model.__class__.__name__)
                )

            # Check that any fields declared on the class are
            # also explicity included in `Meta.fields`.
            missing_fields = set(declared_fields.keys()) - set(fields)
            if missing_fields:
                missing_field = list(missing_fields)[0]
                raise ImproperlyConfigured(
                    'Field `%s` has been declared on serializer `%s`, but '
                    'is missing from `Meta.fields`.' %
                    (missing_field, self.__class__.__name__)
                )

            # Populate any kwargs defined in `Meta.extra_kwargs`
            extras = extra_kwargs.get(field_name, {})
            if extras.get('read_only', False):
                for attr in [
                    'required', 'default', 'allow_blank', 'allow_null',
                    'min_length', 'max_length', 'min_value', 'max_value',
                    'validators', 'queryset'
                ]:
                    kwargs.pop(attr, None)
            kwargs.update(extras)

            if is_links_field:
                self.additional_links[field_name] = field_cls(**kwargs)

            if is_embedded_field:
                self.embedded_fields[field_name] = field_cls(**kwargs)

            # Create the serializer field.
            ret[field_name] = field_cls(**kwargs)

        for field_name, field in unique_fields.items():
            ret[field_name] = field

        # Setup _links field
        if not extra_kwargs.get('url'):
            extra_kwargs['url'] = {}
        if not extra_kwargs['url'].get('lookup_field'):
            extra_kwargs['url']['lookup_field'] = 'pk'

        if extra_kwargs.get('url') and extra_kwargs['url'].get('view_name'):
            view_name = extra_kwargs['url']['view_name']
        else:
            view_name = self._get_default_view_name(self.Meta.model)
        links_field = HALLinksField(
            view_name=view_name,
            lookup_field=extra_kwargs['url']['lookup_field'],
            additional_links=self.additional_links
        )
        ret['_links'] = links_field

        embedded_field = HALEmbeddedField(
            embedded_fields=self.embedded_fields
        )
        ret['_embedded'] = embedded_field

        return ret

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            if field.field_name in self.additional_links.keys() or \
               field.field_name in self.embedded_fields.keys():
                # these will be taken care by the respective HAL fields already
                continue
            if field.field_name in HALfields:
                value = field.to_representation(instance)
            else:
                attribute = field.get_attribute(instance)
                if attribute is None:
                    value = None
                else:
                    value = field.to_representation(attribute)

                transform_method = getattr(self, 'transform_' + field.field_name, None)
                if transform_method is not None:
                    value = transform_method(value)

            ret[field.field_name] = value

        return ret
