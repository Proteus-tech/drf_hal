# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from sample_app.views import PollRetrieveUpdateDestroyAPIView, PollChoiceRetrieveUpdateDestroyAPIView, \
    PollChoiceCreateAPIView, PollRetrieveListAPIView


urlpatterns = patterns('',
    url('^/(?P<pk>\d+)$', PollRetrieveUpdateDestroyAPIView.as_view(), name='poll-detail'),
    url('^s$', PollRetrieveListAPIView.as_view(), name='poll-list'),

    url('^/(?P<poll__pk>\d+)/choice/(?P<pk>\d+)$', PollChoiceRetrieveUpdateDestroyAPIView.as_view(), name='poll-choice-detail'),
    url('^/(?P<poll__pk>\d+)/choice$', PollChoiceCreateAPIView.as_view(), name='create-poll-choice')
)

