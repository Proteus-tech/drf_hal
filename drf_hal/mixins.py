# -*- coding: utf-8 -*-
import urlparse

from django.core.exceptions import ImproperlyConfigured, ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import get_script_prefix, resolve
from django.utils.translation import ugettext_lazy as _
from rest_framework.generics import get_object_or_404


class MultipleLookupFieldsMixin(object):
    lookup_field = ('pk',)

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.
        """
        # Determine the base queryset to use.
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset())
        else:
            pass  # Deprecation warning

        # Perform the lookup filtering.
        if self.lookup_field is not None and isinstance(self.lookup_field, tuple):
            filter_kwargs = {}
            for field in self.lookup_field:
                lookup = self.kwargs.get(field, None)
                filter_kwargs[field] = lookup
        else:
            raise ImproperlyConfigured(
                'Expected view %s to be called with a URL keyword arguments '
                'named %s. Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, ', '.join(self.lookup_field))
            )

        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class LinkInputEmbeddedOutputRelatedSerializerMixin(object):
    """
    This is a bad behavior but we'll support it for now :(
    """
    default_error_messages = {
        'no_match': _('Invalid hyperlink - No URL match'),
        'incorrect_match': _('Invalid hyperlink - Incorrect URL match'),
        'configuration_error': _('Invalid hyperlink due to configuration error'),
        'does_not_exist': _("Invalid hyperlink - object does not exist."),
        'incorrect_type': _('Incorrect type.  Expected url string, received %s.'),
        }

    def from_native(self, data, files):
        value = data
        # Convert URL -> model instance pk
        # TODO: Use values_list
        queryset = self.opts.model.objects.all()
        if queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')

        try:
            http_prefix = value.startswith(('http:', 'https:'))
        except AttributeError:
            msg = self.error_messages['incorrect_type']
            raise ValidationError(msg % type(value).__name__)

        if http_prefix:
            # If needed convert absolute URLs to relative path
            value = urlparse.urlparse(value).path
            prefix = get_script_prefix()
            if value.startswith(prefix):
                value = '/' + value[len(prefix):]

        try:
            match = resolve(value)
        except Exception:
            raise ValidationError(self.error_messages['no_match'])

        if match.view_name != self.view_name:
            raise ValidationError(self.error_messages['incorrect_match'])

        try:
            return self.get_object(queryset, match.view_name,
                                   match.args, match.kwargs)
        except (ObjectDoesNotExist, TypeError, ValueError):
            raise ValidationError(self.error_messages['does_not_exist'])

    def get_object(self, queryset, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.

        Takes the matched URL conf arguments, and the queryset, and should
        return an object instance, or raise an `ObjectDoesNotExist` exception.
        """
        return queryset.get(**view_kwargs)
