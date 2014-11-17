# -*- coding: utf-8 -*-

from django.db.models.fields import FieldDoesNotExist
from rest_framework.serializers import ModelSerializer
from rest_framework.utils import model_meta
from rest_framework.utils.field_mapping import get_field_kwargs, get_nested_relation_kwargs, get_relation_kwargs, \
    get_url_kwargs

# COPIED FROM DRF
# Note: We do the following so that users of the framework can use this style:
#
#     example_field = serializers.CharField(...)
#
# This helps keep the separation between model fields, form fields, and
# serializer fields more explicit.

from rest_framework.relations import *  # NOQA
from rest_framework.fields import *  # NOQA

#
# class HALModelSerializerOptions(HyperlinkedModelSerializerOptions):
#     def __init__(self, meta):
#         super(HALModelSerializerOptions, self).__init__(meta)
#         self.additional_embedded = getattr(meta, 'additional_embedded', None)


class HALModelSerializer(ModelSerializer):
    """
    A subclass of ModelSerializer that follows the HAL specs (http://stateless.co/hal_specification.html).
    """
    # _options_class = HALModelSerializerOptions
    # _default_view_name = '%(model_name)s-detail'
    # _hyperlink_field_class = HyperlinkedRelatedField
    #
    #
    # def __init__(self, *args, **kwargs):
    #     self.additional_links = {}
    #     self.embedded_fields = {}
    #
    #     super(HALModelSerializer, self).__init__(*args, **kwargs)
    #
    #     if self.Meta.view_name is None:
    #         self.Meta.view_name = self._get_default_view_name(self.opts.model)
    #
    #     _links = HALLinksField(
    #         view_name=self.opts.view_name,
    #         lookup_field=self.opts.lookup_field,
    #         additional_links=self.additional_links,
    #         )
    #     _links.initialize(self, '_links')
    #     self.fields['_links'] = _links
    #
    #     if self.embedded_fields:
    #         _embedded = HALEmbeddedField(
    #             embedded_fields=self.embedded_fields,
    #             )
    #         _embedded.initialize(self, '_embedded')
    #         self.fields['_embedded'] = _embedded

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
            if field_name in declared_fields:
                # Field is explicitly declared on the class, use that.
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
                else:
                    field_cls = self._related_class
                    kwargs = get_relation_kwargs(field_name, relation_info)
                    # `view_name` is only valid for hyperlinked relationships.
                    if not issubclass(field_cls, HyperlinkedRelatedField):
                        kwargs.pop('view_name', None)

            elif hasattr(model, field_name):
                # Create a read only field for model methods and properties.
                field_cls = ReadOnlyField
                kwargs = {}

            elif field_name == api_settings.URL_FIELD_NAME:
                # Create the URL field.
                field_cls = HyperlinkedIdentityField
                kwargs = get_url_kwargs(model)

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

            # Create the serializer field.
            ret[field_name] = field_cls(**kwargs)

        for field_name, field in unique_fields.items():
            ret[field_name] = field

        return ret

    # def get_default_fields(self, base_fields):
    #     """
    #     Return all the fields that should be serialized for the model.
    #     """
    #
    #     cls = self.opts.model
    #     assert cls is not None, \
    #         "Serializer class '%s' is missing 'model' Meta option" % self.__class__.__name__
    #     opts = get_concrete_model(cls)._meta
    #     ret = SortedDict()
    #     nested = bool(self.opts.depth)
    #
    #     # Deal with adding the primary key field
    #     pk_field = opts.pk
    #     while pk_field.rel and pk_field.rel.parent_link:
    #         # If model is a child via multitable inheritance, use parent's pk
    #         pk_field = pk_field.rel.to._meta.pk
    #
    #     field = self.get_pk_field(pk_field)
    #     if field:
    #         ret[pk_field.name] = field
    #
    #     # Deal with forward relationships
    #     forward_rels = [field for field in opts.fields if field.serialize]
    #     forward_rels += [field for field in opts.many_to_many if field.serialize]
    #
    #     for model_field in forward_rels:
    #         field = None
    #         has_through_model = False
    #
    #         if model_field.rel:
    #             to_many = isinstance(model_field,
    #                                  models.fields.related.ManyToManyField)
    #             related_model = _resolve_model(model_field.rel.to)
    #
    #             if to_many and not model_field.rel.through._meta.auto_created:
    #                 has_through_model = True
    #
    #         if model_field.rel and nested:
    #             self.add_field_to_embedded(model_field.name, self.get_nested_field(model_field, related_model, to_many))
    #         elif model_field.rel and model_field.name in base_fields:
    #             key = model_field.name
    #             self.add_field_to_embedded(key, base_fields[key])
    #             base_fields.pop(key)
    #         elif model_field.rel:
    #             self.add_field_to_links(model_field.name, self.get_related_field(model_field, related_model, to_many))
    #         else:
    #             field = self.get_field(model_field)
    #
    #         if field:
    #             if has_through_model:
    #                 field.read_only = True
    #
    #             ret[model_field.name] = field
    #
    #     # Deal with reverse relationships
    #     reverse_rels = opts.get_all_related_objects()
    #     reverse_rels += opts.get_all_related_many_to_many_objects()
    #
    #     for relation in reverse_rels:
    #         accessor_name = relation.get_accessor_name()
    #         if accessor_name not in self.opts.fields and accessor_name not in base_fields:
    #             continue
    #         related_model = relation.model
    #         to_many = relation.field.rel.multiple
    #         has_through_model = False
    #         is_m2m = isinstance(relation.field,
    #                             models.fields.related.ManyToManyField)
    #
    #         if (is_m2m and
    #                 hasattr(relation.field.rel, 'through') and
    #                 not relation.field.rel.through._meta.auto_created):
    #             has_through_model = True
    #
    #         if nested:
    #             field = self.get_nested_field(None, related_model, to_many)
    #         elif accessor_name in base_fields:
    #             field = base_fields[accessor_name]
    #             base_fields.pop(accessor_name)
    #         else:
    #             field = self.get_related_field(None, related_model, to_many)
    #
    #         if field:
    #             self.add_field_to_embedded(accessor_name, field, has_through_model)
    #
    #     # Add the `read_only` flag to any fields that have bee specified
    #     # in the `read_only_fields` option
    #     for field_name in self.opts.read_only_fields:
    #         assert field_name not in self.base_fields.keys(), (
    #             "field '%s' on serializer '%s' specified in "
    #             "`read_only_fields`, but also added "
    #             "as an explicit field.  Remove it from `read_only_fields`." %
    #             (field_name, self.__class__.__name__))
    #         assert field_name in ret, (
    #             "Non-existant field '%s' specified in `read_only_fields` "
    #             "on serializer '%s'." %
    #             (field_name, self.__class__.__name__))
    #         ret[field_name].read_only = True
    #
    #     for field_name in self.opts.write_only_fields:
    #         assert field_name not in self.base_fields.keys(), (
    #             "field '%s' on serializer '%s' specified in "
    #             "`write_only_fields`, but also added "
    #             "as an explicit field.  Remove it from `write_only_fields`." %
    #             (field_name, self.__class__.__name__))
    #         assert field_name in ret, (
    #             "Non-existant field '%s' specified in `write_only_fields` "
    #             "on serializer '%s'." %
    #             (field_name, self.__class__.__name__))
    #         ret[field_name].write_only = True
    #
    #     return ret
    #
    # def get_fields(self):
    #     """
    #     Returns the complete set of fields for the object as a dict.
    #
    #     This will be the set of any explicitly declared fields,
    #     plus the set of fields returned by get_default_fields().
    #     """
    #     ret = SortedDict()
    #
    #     # Get the explicitly declared fields
    #     base_fields = copy.deepcopy(self.base_fields)
    #     for key, field in base_fields.items():
    #         if isinstance(field, HALLinkField) or isinstance(field, HALRelatedLinkField):
    #             self.add_field_to_links(key, field)
    #         else:
    #             ret[key] = field
    #
    #     # Add in the default fields
    #     default_fields = self.get_default_fields(ret)
    #     for key, val in default_fields.items():
    #         if key not in ret:
    #             ret[key] = val
    #
    #     # If 'fields' is specified, use those fields, in that order.
    #     if self.opts.fields:
    #         assert isinstance(self.opts.fields, (list, tuple)), '`fields` must be a list or tuple'
    #         new = SortedDict()
    #         for key in self.opts.fields:
    #             new[key] = ret[key]
    #         ret = new
    #
    #     # Remove anything in 'exclude'
    #     if self.opts.exclude:
    #         assert isinstance(self.opts.exclude, (list, tuple)), '`exclude` must be a list or tuple'
    #         for key in self.opts.exclude:
    #             ret.pop(key, None)
    #             self.additional_links.pop(key, None)
    #             self.embedded_fields.pop(key, None)
    #
    #     # additional embedded fields
    #     if getattr(self.opts, 'additional_embedded', None):
    #         assert isinstance(self.opts.additional_embedded, (list, tuple)), '`exclude` must be a list or tuple'
    #         for key in self.opts.additional_embedded:
    #             field = ret.pop(key, None)
    #             if field:
    #                 self.add_field_to_embedded(key, field)
    #
    #     for key, field in ret.items():
    #         field.initialize(parent=self, field_name=key)
    #
    #     return ret
    #
    # def restore_initialize_field(self, field_name, field, data, files, reverted_data):
    #     field.initialize(parent=self, field_name=field_name)
    #     try:
    #         field.field_from_native(data, files, field_name, reverted_data)
    #     except ValidationError as err:
    #         if getattr(err, 'error_dict', None):
    #             for key, value in err.error_dict.items():
    #                 self._errors[key] = value.messages
    #         else:
    #             self._errors[field_name] = list(err.messages)
    #
    # def restore_fields(self, data, files):
    #     """
    #     Core of deserialization, together with `restore_object`.
    #     Converts a dictionary of data into a dictionary of deserialized fields.
    #     """
    #     reverted_data = {}
    #     copy_data = data.copy()
    #
    #     if data is not None and not isinstance(data, dict):
    #         self._errors['non_field_errors'] = ['Invalid data']
    #         return None
    #
    #     for field_name, field in self.fields.items():
    #         copy_data.pop(field_name, None)
    #         self.restore_initialize_field(field_name, field, data, files, reverted_data)
    #
    #     # what's left of the data
    #     cls = self.opts.model
    #     assert cls is not None, \
    #         "Serializer class '%s' is missing 'model' Meta option" % self.__class__.__name__
    #     opts = get_concrete_model(cls)._meta
    #     nested = bool(self.opts.depth)
    #     for field_name in data.keys():
    #         try:
    #             model_field_tuple = opts.get_field_by_name(field_name)
    #             model_field = model_field_tuple[0]
    #         except models.FieldDoesNotExist:
    #             continue
    #         if model_field.rel:
    #             related_model = _resolve_model(model_field.rel.to)
    #             to_many = isinstance(model_field,
    #                                  models.fields.related.ManyToManyField)
    #             if nested:
    #                 field = self.get_nested_field(model_field, related_model, to_many)
    #             else:
    #                 field = self.get_related_field(model_field, related_model, to_many)
    #             self.restore_initialize_field(field_name, field, data, files, reverted_data)
    #
    #     return reverted_data

