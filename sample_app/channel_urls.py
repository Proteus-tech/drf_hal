# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from sample_app.views import CreateChannelAPIView, ChannelRetrieveUpdateDestroyAPIView


urlpatterns = patterns(
    '',
    url('^$', CreateChannelAPIView.as_view(),
       name='create-channel'),
    url('^/(?P<pk>\d+)$', ChannelRetrieveUpdateDestroyAPIView.as_view(),
        name='channel-detail'),
)
