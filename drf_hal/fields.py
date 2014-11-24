# -*- coding: utf-8 -*-
import warnings

from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch
from rest_framework.fields import Field
from rest_framework import reverse
from rest_framework.relations import HyperlinkedRelatedField, ManyRelatedField


class HALRelatedLinkField(HyperlinkedRelatedField):
    many = False

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except KeyError:
            msg = "HALLinkField requires 'view_name' argument"
            raise ValueError(msg)

        self.lookup_field = kwargs.pop('lookup_field')
        self.many = kwargs.pop('many', self.many)
        self.format = kwargs.pop('format', None)
        super(HyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        kwargs = {}
        if self.lookup_field:
            for lookup_field in self.lookup_field:
                split_lookup_field = lookup_field.split('__')
                if len(split_lookup_field) > 1:
                    value = obj
                    for field in split_lookup_field:
                        value = getattr(value, field, None)
                    kwargs[lookup_field] = value
                else:
                    kwargs[lookup_field] = getattr(obj, lookup_field, None)

        try:
            return reverse.reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        raise NoReverseMatch()


class HALLinksField(Field):
    """
    Represents the instance, or a property on the instance, using hyperlinking.
    """
    lookup_field = 'pk'

    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, 'The `view_name` argument is required.'
        self.view_name = view_name
        self.lookup_field = kwargs.pop('lookup_field', self.lookup_field)
        self.lookup_url_kwarg = kwargs.pop('lookup_url_kwarg', self.lookup_field)
        self.format = kwargs.pop('format', None)

        self.additional_links = kwargs.pop('additional_links', {})

        super(HALLinksField, self).__init__(view_name, **kwargs)

        self.read_only = True

    def to_representation(self, value):
        request = self.context.get('request', None)
        format = self.context.get('format', None)
        view_name = self.view_name

        if request is None:
            warnings.warn("Using `HALLinksField` without including the "
                          "request in the serializer context is not allowed. "
                          "Add `context={'request': request}` when instantiating the serializer.",
                          RuntimeWarning, stacklevel=4)

        # By default use whatever format is given for the current context
        # unless the target is a different type to the source.
        #
        # Eg. Consider a HyperlinkedIdentityField pointing from a json
        # representation to an html property of that representation...
        #
        # '/snippets/1/' should link to '/snippets/1/highlight/'
        # ...but...
        # '/snippets/1/.json' should link to '/snippets/1/highlight/.html'
        if format and self.format and self.format != format:
            format = self.format

        # Return the hyperlink, or error if incorrectly configured.
        try:
            self_link = self.get_url(value, view_name, request, format)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            raise Exception(msg % view_name)

        ret = {
            'self': {
                'href': self_link
            }
        }
        for key, field in self.additional_links.items():
            if not field.source:
                # not previously bound
                field.bind(key, self.parent)
            attribute = field.get_attribute(value)
            if isinstance(field, ManyRelatedField):
                ret[key] = [{'href': link} for link in field.to_representation(attribute)]
            else:
                ret[key] = {
                    'href': field.to_representation(attribute)
                }
        return ret

    def __get_lookup_value(self, obj, lookup_field):
        split_lookup_field = lookup_field.split('__')
        if len(split_lookup_field) > 1:
            value = obj
            for field in split_lookup_field:
                value = getattr(value, field, None)
            lookup = value
        else:
            lookup = getattr(obj, lookup_field, None)
        return lookup

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        if isinstance(self.lookup_field, tuple):
            lookup_fields = self.lookup_field
            kwargs = {}
            for lookup_field in lookup_fields:
                kwargs[lookup_field] = self.__get_lookup_value(obj, lookup_field)
        else:
            lookup_field = self.__get_lookup_value(obj, self.lookup_field)
            kwargs = {self.lookup_field: lookup_field}

        # Handle unsaved object case
        if lookup_field is None:
            return None

        try:
            return reverse.reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        raise NoReverseMatch()


class HALEmbeddedFieldValidationError(ValidationError):
    def __init__(self, error_dict):
        self.error_dict = error_dict


class HALEmbeddedField(Field):

    def __init__(self, *args, **kwargs):
        self.embedded_fields = kwargs.pop('embedded_fields', {})

        super(HALEmbeddedField, self).__init__(*args, **kwargs)

        self.read_only = True

    def to_representation(self, value):
        ret = {}
        for field_name, field in self.embedded_fields.items():
            attribute = field.get_attribute(value)
            if getattr(field, 'many', None):
                attribute = attribute.all()
            if attribute is None:
                value = None
            else:
                value = field.to_representation(attribute)

            transform_method = getattr(self, 'transform_' + field.field_name, None)
            if transform_method is not None:
                value = transform_method(value)
            ret[field_name] = value
        return ret



