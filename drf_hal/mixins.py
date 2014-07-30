# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
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

        print filter_kwargs
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
