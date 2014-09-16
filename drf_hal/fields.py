# -*- coding: utf-8 -*-
import warnings

from django.core.urlresolvers import NoReverseMatch
from rest_framework.fields import Field
from rest_framework import reverse
from rest_framework.relations import HyperlinkedRelatedField


class HALLinkField(Field):
    many = False

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except KeyError:
            msg = "HALLinkField requires 'view_name' argument"
            raise ValueError(msg)

        self.lookup_mapping = kwargs.pop('lookup_mapping')
        self.many = kwargs.pop('many', self.many)
        super(HALLinkField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        request = self.context.get('request')
        kwargs = {}
        for key, value in self.lookup_mapping.items():
            kwargs[key] = getattr(obj, value, None)
        return reverse.reverse(self.view_name, kwargs=kwargs, request=request)


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
    read_only = True

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except KeyError:
            msg = "HALLinksField requires 'view_name' argument"
            raise ValueError(msg)

        self.additional_links = kwargs.pop('additional_links', {})
        self.exclude = kwargs.pop('exclude', ())

        self.format = kwargs.pop('format', None)
        lookup_field = kwargs.pop('lookup_field', None)
        self.lookup_field = lookup_field or self.lookup_field

        super(HALLinksField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
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
            self_link = self.get_url(obj, view_name, request, format)
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
            field.initialize(parent=self, field_name=key)
            if field.many:
                links = field.field_to_native(obj, key)
                ret[key] = [{'href': link} for link in links]
            else:
                ret[key] = {
                    'href': field.field_to_native(obj, key)
                }
        return ret

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
                split_lookup_field = lookup_field.split('__')
                if len(split_lookup_field) > 1:
                    value = obj
                    for field in split_lookup_field:
                        value = getattr(value, field, None)
                    kwargs[lookup_field] = value
                else:
                    kwargs[lookup_field] = getattr(obj, lookup_field, None)
        else:
            lookup_field = getattr(obj, self.lookup_field, None)
            kwargs = {self.lookup_field: lookup_field}

        # Handle unsaved object case
        if lookup_field is None:
            return None

        try:
            return reverse.reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        raise NoReverseMatch()


class HALEmbeddedField(Field):

    def __init__(self, *args, **kwargs):
        self.embedded_fields = kwargs.pop('embedded_fields', {})

        super(HALEmbeddedField, self).__init__(*args, **kwargs)

    def initialize(self, parent, field_name):
        [field.initialize(parent, name) for name, field in self.embedded_fields.items()]
        return super(HALEmbeddedField, self).initialize(parent, field_name)

    def field_to_native(self, obj, field_name):
        ret = {}
        [ret.update({key: field.field_to_native(obj, key)}) for key, field in self.embedded_fields.items()]
        return ret

    def field_from_native(self, data, files, field_name, into):
        embedded_data = data.get(field_name)
        if not embedded_data:
            return
        [field.field_from_native(embedded_data, files, key, into) for key, field in self.embedded_fields.items()]

