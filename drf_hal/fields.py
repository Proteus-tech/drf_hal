# -*- coding: utf-8 -*-
import warnings
from django.core.urlresolvers import NoReverseMatch, reverse
from rest_framework.fields import Field


class HalLinksField(Field):
    """
    Represents the instance, or a property on the instance, using hyperlinking.
    """
    lookup_field = 'pk'
    read_only = True

    # These are all pending deprecation
    pk_url_kwarg = 'pk'
    slug_field = 'slug'
    slug_url_kwarg = None  # Defaults to same as `slug_field` unless overridden

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except KeyError:
            msg = "HyperlinkedIdentityField requires 'view_name' argument"
            raise ValueError(msg)

        self.format = kwargs.pop('format', None)
        lookup_field = kwargs.pop('lookup_field', None)
        self.lookup_field = lookup_field or self.lookup_field

        # These are pending deprecation
        if 'pk_url_kwarg' in kwargs:
            msg = 'pk_url_kwarg is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
        if 'slug_url_kwarg' in kwargs:
            msg = 'slug_url_kwarg is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
        if 'slug_field' in kwargs:
            msg = 'slug_field is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)

        self.slug_field = kwargs.pop('slug_field', self.slug_field)
        default_slug_kwarg = self.slug_url_kwarg or self.slug_field
        self.pk_url_kwarg = kwargs.pop('pk_url_kwarg', self.pk_url_kwarg)
        self.slug_url_kwarg = kwargs.pop('slug_url_kwarg', default_slug_kwarg)

        super(HalLinksField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        request = self.context.get('request', None)
        format = self.context.get('format', None)
        view_name = self.view_name

        if request is None:
            warnings.warn("Using `HyperlinkedIdentityField` without including the "
                          "request in the serializer context is deprecated. "
                          "Add `context={'request': request}` when instantiating the serializer.",
                          DeprecationWarning, stacklevel=4)

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
            return self.get_url(obj, view_name, request, format)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            raise Exception(msg % view_name)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        lookup_field = getattr(obj, self.lookup_field, None)
        kwargs = {self.lookup_field: lookup_field}

        # Handle unsaved object case
        if lookup_field is None:
            return None

        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        if self.pk_url_kwarg != 'pk':
            # Only try pk lookup if it has been explicitly set.
            # Otherwise, the default `lookup_field = 'pk'` has us covered.
            kwargs = {self.pk_url_kwarg: obj.pk}
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        slug = getattr(obj, self.slug_field, None)
        if slug:
            # Only use slug lookup if a slug field exists on the model
            kwargs = {self.slug_url_kwarg: slug}
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        raise NoReverseMatch()


class HalEmbeddedField(Field):
    pass
