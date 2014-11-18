# -*- coding: utf-8 -*-

from rest_framework.serializers import ModelSerializer

# COPIED FROM DRF
# Note: We do the following so that users of the framework can use this style:
#
#     example_field = serializers.CharField(...)
#
# This helps keep the separation between model fields, form fields, and
# serializer fields more explicit.

from rest_framework.fields import *  # NOQA

#
# class HALModelSerializerOptions(HyperlinkedModelSerializerOptions):
#     def __init__(self, meta):
#         super(HALModelSerializerOptions, self).__init__(meta)
#         self.additional_embedded = getattr(meta, 'additional_embedded', None)
from drf_hal.fields import HALLinksField


class HALModelSerializer(ModelSerializer):
    """
    A subclass of ModelSerializer that follows the HAL specs (http://stateless.co/hal_specification.html).
    """
    # _options_class = HALModelSerializerOptions
    _default_view_name = '%(model_name)s-detail'
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
        ret = super(HALModelSerializer, self).get_fields()
        extra_kwargs = getattr(self.Meta, 'extra_kwargs', {})

        if not extra_kwargs.get('url'):
            extra_kwargs['url'] = {}
        if not extra_kwargs['url'].get('lookup_field'):
            extra_kwargs['url']['lookup_field'] = 'pk'

        if extra_kwargs.get('url') and extra_kwargs['url'].get('view_name'):
            view_name = extra_kwargs['url']['view_name']
        else:
            view_name = self._get_default_view_name(self.Meta.model)
        _links = HALLinksField(
            view_name=view_name,
            lookup_field=extra_kwargs['url']['lookup_field'],
            # additional_links=self.additional_links,
        )
        self.fields['_links'] = _links

        return ret

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            if field.field_name == '_links':
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
