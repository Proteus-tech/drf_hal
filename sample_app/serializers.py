# -*- coding: utf-8 -*-
from drf_hal.serializers import HALModelSerializer
from sample_app.models import Choice, Poll


class PollSerializer(HALModelSerializer):
    class Meta:
        model = Poll


class ChoiceSerializer(HALModelSerializer):
    class Meta:
        model = Choice


class ChoiceExcludePollSerializer(HALModelSerializer):
    class Meta:
        model = Choice
        exclude = ('poll',)


class ChoiceExcludeVotesSerializer(HALModelSerializer):
    class Meta:
        model = Choice
        exclude = ('votes',)


class ChoiceEmbedPollSerializer(HALModelSerializer):
    poll = PollSerializer()

    class Meta:
        model = Choice


class ChoiceFieldsPollSerializer(HALModelSerializer):

    class Meta:
        model = Choice
        fields = ('id', 'choice_text',)


class ChoiceLookupFieldPollSerializer(HALModelSerializer):

    class Meta:
        model = Choice
        lookup_field = 'pk'
