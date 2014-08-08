# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework import pagination
from rest_framework.templatetags.rest_framework import replace_query_param


class PageLinkMixin(object):
    page_field = 'page'

    def _get_page_link(self, value, page):
        if not value.paginator.num_pages:
            return None
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return {
            'href': replace_query_param(url, self.page_field, page)
        }


class SelfPageField(PageLinkMixin, serializers.Field):
    """
    Field that returns a link to the current page.
    """
    def to_native(self, value):
        return self._get_page_link(value, value.number)


class FirstPageField(PageLinkMixin, serializers.Field):
    """
    Field that returns a link to the first page in paginated results.
    """
    def to_native(self, value):
        return self._get_page_link(value, None)


class LastPageField(PageLinkMixin, serializers.Field):
    """
    Field that returns a link to the last page in paginated results.
    """
    page_field = 'page'

    def to_native(self, value):
        return self._get_page_link(value, value.paginator.num_pages)


class HALPaginationLinksSerializer(serializers.Serializer):
    self = SelfPageField(source='*')
    next = pagination.NextPageField(source='*')
    prev = pagination.PreviousPageField(source='*')
    first = FirstPageField(source='*')
    last = LastPageField(source='*')


class HALPaginationSerializer(pagination.BasePaginationSerializer):
    _links = HALPaginationLinksSerializer(source='*')  # Takes the page object as the source
    total = serializers.Field(source='paginator.count')

    def __init__(self, *args, **kwargs):
        """
        Override init to add in the embedded field on-the-fly.
        """
        super(pagination.BasePaginationSerializer, self).__init__(*args, **kwargs)
        view = self.context['view']
        self.results_field = unicode(view.model._meta.verbose_name_plural)
        object_serializer = self.opts.object_serializer_class

        if 'context' in kwargs:
            context_kwarg = {'context': kwargs['context']}
        else:
            context_kwarg = {}

        self.fields[self.results_field] = object_serializer(source='object_list', **context_kwarg)

    def to_native(self, obj):
        native = super(HALPaginationSerializer, self).to_native(obj)
        results = native.pop(self.results_field, None)
        native['_embedded'] = {
            self.results_field: results
        }
        return native

