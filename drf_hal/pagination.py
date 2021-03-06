# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework import pagination
from rest_framework.templatetags.rest_framework import replace_query_param


class PageLinkMixin(object):
    page_field = 'page'

    def _get_current_uri(self):
        request = self.context.get('request')
        return request and request.build_absolute_uri() or ''

    def _get_link_object(self, link):
        return {
            'href': link
        }

    def _get_page_link(self, value, page):
        if not value.paginator.count:
            return None
        uri = self._get_current_uri()
        return self._get_link_object(replace_query_param(uri, self.page_field, page))


class SelfPageField(PageLinkMixin, serializers.Field):
    """
    Field that returns a link to the current page.
    """
    def to_native(self, value):
        return self._get_link_object(self._get_current_uri())


class FirstPageField(PageLinkMixin, serializers.Field):
    """
    Field that returns a link to the first page in paginated results.
    """
    def to_native(self, value):
        return self._get_page_link(value, 1)


class LastPageField(PageLinkMixin, serializers.Field):
    """
    Field that returns a link to the last page in paginated results.
    """
    def to_native(self, value):
        return self._get_page_link(value, value.paginator.num_pages)


class NextPageField(PageLinkMixin, serializers.Field):
    """
    Field that returns a link to the next page in paginated results.
    """
    def to_native(self, value):
        if not value.has_next():
            return None
        return self._get_page_link(value, value.next_page_number())


class PreviousPageField(PageLinkMixin, serializers.Field):
    """
    Field that returns a link to the next page in paginated results.
    """
    def to_native(self, value):
        if not value.has_previous():
            return None
        return self._get_page_link(value, value.previous_page_number())


class CountField(serializers.Field):
    """
    Field that returns count for the page
    """
    def to_native(self, value):
        if value.paginator.count == 0:
            return 0
        start_index = value.start_index()
        end_index = value.end_index()
        return (end_index - start_index) + 1


class HALPaginationLinksSerializer(serializers.Serializer):
    self = SelfPageField(source='*')
    next = NextPageField(source='*')
    prev = PreviousPageField(source='*')
    first = FirstPageField(source='*')
    last = LastPageField(source='*')


class HALPaginationSerializer(pagination.BasePaginationSerializer):
    _links = HALPaginationLinksSerializer(source='*')  # Takes the page object as the source
    total = serializers.Field(source='paginator.count')
    num_pages = serializers.Field(source='paginator.num_pages')
    count = CountField(source='*')

    def __init__(self, *args, **kwargs):
        """
        Override init to add in the embedded field on-the-fly.
        """
        super(pagination.BasePaginationSerializer, self).__init__(*args, **kwargs)
        view = self.context['view']
        self.results_field = unicode(view.model._meta.verbose_name_plural)
        object_serializer = self.opts.object_serializer_class

        context_kwarg = {'context': self.context}
        self.fields[self.results_field] = object_serializer(source='object_list', **context_kwarg)

    def to_native(self, obj):
        native = super(HALPaginationSerializer, self).to_native(obj)
        results = native.pop(self.results_field, None)
        native['_embedded'] = {
            self.results_field: results
        }
        return native

