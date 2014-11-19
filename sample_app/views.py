# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.reverse import reverse

from drf_hal.mixins import MultipleLookupFieldsMixin
from sample_app.models import Choice, Poll, Channel, Partner, UserProfile
from sample_app.serializers import ChoiceSerializer, ChoiceExcludePollSerializer, ChoiceExcludeVotesSerializer, \
    ChoiceEmbedPollSerializer, PollSerializer, ChoiceFieldsPollSerializer, ChoiceLookupFieldPollSerializer, \
    PollChoiceSerializer, PollListSerializer, ChannelSerializer, PartnerSerializer, CreatePollWithChoicesSerializer, \
    PollWithAdditionalEmbeddedSerializer, UserSerializer, UserProfileSerializer


class ChoiceRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Choice.objects.all()

    def get_serializer_class(self):
        query_params = self.request.QUERY_PARAMS
        if query_params.get('exclude'):
            exclude = query_params['exclude']
            if exclude == 'poll':
                return ChoiceExcludePollSerializer
            return ChoiceExcludeVotesSerializer
        if query_params.get('embed'):
            return ChoiceEmbedPollSerializer
        if query_params.get('fields'):
            return ChoiceFieldsPollSerializer
        if query_params.get('lookup_field'):
            return ChoiceLookupFieldPollSerializer
        return ChoiceSerializer


class CreatePollWithChoicesAPIView(CreateAPIView):
    model = Poll
    serializer_class = CreatePollWithChoicesSerializer


class PollRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Poll.objects.all()

    def get_serializer_class(self):
        return PollSerializer


class PollWithAdditionalEmbeddedView(RetrieveAPIView):
    queryset = Poll.objects.all()

    def get_serializer_class(self):
        return PollWithAdditionalEmbeddedSerializer


class PollRetrieveListAPIView(ListAPIView):
    model = Poll
    serializer_class = PollSerializer
    pagination_serializer_class = PollListSerializer


class PollChoiceRetrieveUpdateDestroyAPIView(MultipleLookupFieldsMixin, RetrieveUpdateDestroyAPIView):
    queryset = Choice.objects.all()
    lookup_field = ('poll__pk', 'pk')
    serializer_class = PollChoiceSerializer


class PollChoiceCreateAPIView(CreateAPIView):
    model = Choice
    serializer_class = PollChoiceSerializer

    def create(self, request, *args, **kwargs):
        request.DATA['poll'] = reverse('poll-detail', kwargs={'pk': kwargs['poll__pk']}, request=request)
        return super(PollChoiceCreateAPIView, self).create(request, *args, **kwargs)


class PollListAPIView(ListAPIView):
    model = Poll
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100


class CreateChannelAPIView(CreateAPIView):
    model = Channel
    serializer_class = ChannelSerializer


class ChannelRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    model = Channel
    serializer_class = ChannelSerializer


class PartnerRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    model = Partner
    serializer_class = PartnerSerializer


class UserView(RetrieveAPIView):
    model = get_user_model()
    serializer_class = UserSerializer
    lookup_field = 'username'


class UserProfileView(RetrieveAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'user__username'
