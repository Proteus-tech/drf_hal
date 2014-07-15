# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from sample_app.views import PollRetrieveUpdateDestroyAPIView


urlpatterns = patterns('',
   url('^/(?P<pk>\d+)$', PollRetrieveUpdateDestroyAPIView.as_view(),
       name='poll-detail')
)

