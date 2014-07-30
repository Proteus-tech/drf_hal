# -*- coding: utf-8 -*-
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from drf_hal.mixins import MultipleLookupFieldsMixin
from sample_app.models import Choice, Poll
from sample_app.serializers import ChoiceSerializer, ChoiceExcludePollSerializer, ChoiceExcludeVotesSerializer, \
    ChoiceEmbedPollSerializer, PollSerializer, ChoiceFieldsPollSerializer, ChoiceLookupFieldPollSerializer, \
    PollChoiceSerializer


class ChoiceRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    model = Choice

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


class PollRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    model = Poll

    def get_serializer_class(self):
        return PollSerializer


class PollChoiceRetrieveUpdateDestroyAPIView(MultipleLookupFieldsMixin, RetrieveUpdateDestroyAPIView):
    model = Choice
    lookup_field = ('poll__pk', 'pk')
    serializer_class = PollChoiceSerializer

