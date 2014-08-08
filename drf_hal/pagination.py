# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework import pagination
from rest_framework.templatetags.rest_framework import replace_query_param


class FirstPageField(serializers.Field):
    """
    Field that returns a link to the first page in paginated results.
    """
    page_field = 'page'

    def to_native(self, value):
        if not value.paginator.num_pages:
            return None
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return url


class LastPageField(serializers.Field):
    """
    Field that returns a link to the last page in paginated results.
    """
    page_field = 'page'

    def to_native(self, value):
        if not value.paginator.num_pages:
            return None
        page = value.paginator.num_pages
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return replace_query_param(url, self.page_field, page)


class HALPaginationLinksSerializer(serializers.Serializer):
    next = pagination.NextPageField(source='*')
    prev = pagination.PreviousPageField(source='*')
    first = FirstPageField(source='*')
    last = LastPageField(source='*')


class HALPaginationSerializer(pagination.BasePaginationSerializer):
    _links = HALPaginationLinksSerializer(source='*')  # Takes the page object as the source
    total = serializers.Field(source='paginator.count')

    results_field = 'objects'
