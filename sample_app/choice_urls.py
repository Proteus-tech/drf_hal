# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from sample_app.views import ChoiceRetrieveUpdateDestroyAPIView


urlpatterns = patterns('',
    url('^/(?P<pk>\d+)$', ChoiceRetrieveUpdateDestroyAPIView.as_view(), name='choice-detail')
)

