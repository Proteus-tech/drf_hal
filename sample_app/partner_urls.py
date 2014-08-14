# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from sample_app.views import PartnerRetrieveUpdateDestroyAPIView


urlpatterns = patterns(
    '',
    url('^/(?P<pk>\d+)$', PartnerRetrieveUpdateDestroyAPIView.as_view(),
        name='partner-detail'),
    )

