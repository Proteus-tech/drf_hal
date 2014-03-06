# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from sample_app.models import Poll


urlpatterns = patterns('',
   url('^/(?P<pk>\d+)$', RetrieveUpdateDestroyAPIView.as_view(model=Poll),
       name='poll-detail')
)

