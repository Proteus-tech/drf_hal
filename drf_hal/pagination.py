# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework import pagination


class HALPaginationLinksSerializer(serializers.Serializer):
    next = pagination.NextPageField(source='*')
    prev = pagination.PreviousPageField(source='*')


class HALPaginationSerializer(pagination.BasePaginationSerializer):
    _links = HALPaginationLinksSerializer(source='*')  # Takes the page object as the source
    total = serializers.Field(source='paginator.count')

    results_field = 'objects'
