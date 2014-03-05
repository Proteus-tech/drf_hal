# -*- coding: utf-8 -*-
from rest_framework.fields import Field
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import ModelSerializer, HyperlinkedModelSerializerOptions
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
        super(HalModelSerializer, self).__init__(*args, **kwargs)

        if self.opts.view_name is None:
            self.opts.view_name = self._get_default_view_name(self.opts.model)

        _links = HalLinksField(
            view_name=self.opts.view_name
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
    #
    # def get_related_field(self, model_field, related_model, to_many):
    #     """
    #     Creates a default instance of a flat relational field.
    #     """
    #     # TODO: filter queryset using:
    #     # .using(db).complex_filter(self.rel.limit_choices_to)
    #     kwargs = {
    #         'queryset': related_model._default_manager,
    #         'view_name': self._get_default_view_name(related_model),
    #         'many': to_many
    #     }
    #
    #     if model_field:
    #         kwargs['required'] = not(model_field.null or model_field.blank)
    #
    #     if self.opts.lookup_field:
    #         kwargs['lookup_field'] = self.opts.lookup_field
    #
    #     return self._hyperlink_field_class(**kwargs)

    def get_identity(self, data):
        """
        This hook is required for bulk update.
        We need to override the default, to use the _links as the identity.
        """
        try:
            return data.get('_links', None) and data['links'].get('self') and data['links']['self'].get('href')
        except AttributeError:
            return None

