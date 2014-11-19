# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns

from sample_app.views import UserView, UserProfileView


urlpatterns = patterns(
    '',
    url(r'^/(?P<username>[-\w]+)$', UserView.as_view(), name='user-detail'),
    url(r'^/(?P<user__username>[-\w]+)/profile$', UserProfileView.as_view(), name='userprofile-detail'),
)
