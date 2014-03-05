# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from sample_app.models import Choice
from sample_app.serializers import ChoiceSerializer


urlpatterns = patterns('',
    url('^/(?P<pk>\d+)$', RetrieveUpdateDestroyAPIView.as_view(model=Choice, serializer_class=ChoiceSerializer),
        name='choice-detail')
)

