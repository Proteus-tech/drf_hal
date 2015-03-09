# -*- coding: utf-8 -*-
from rest_framework import filters

class ViewKwargsFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        return queryset.filter(**view.kwargs)
