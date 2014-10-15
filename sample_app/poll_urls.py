# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from sample_app.views import PollRetrieveUpdateDestroyAPIView, PollChoiceRetrieveUpdateDestroyAPIView, \
    PollChoiceCreateAPIView, PollListAPIView, CreatePollWithChoicesAPIView, PollWithAdditionalEmbeddedView


urlpatterns = patterns(
    '',
    url('^_with_choices$', CreatePollWithChoicesAPIView.as_view(),
       name='poll-with-choices'),
    url('^_with_additional_embedded/(?P<pk>\d+)$', PollWithAdditionalEmbeddedView.as_view(),
        name='poll-with-additional-embedded'),
    url('^/(?P<pk>\d+)$', PollRetrieveUpdateDestroyAPIView.as_view(),
       name='poll-detail'),
    url('^/(?P<poll__pk>\d+)/choice/(?P<pk>\d+)$', PollChoiceRetrieveUpdateDestroyAPIView.as_view(), name='poll-choice-detail'),
    url('^/(?P<poll__pk>\d+)/choice$', PollChoiceCreateAPIView.as_view(), name='create-poll-choice'),
    url('^s$', PollListAPIView.as_view(), name='poll-list')
)

