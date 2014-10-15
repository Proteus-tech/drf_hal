# -*- coding: utf-8 -*-
from rest_framework import serializers

from drf_hal.pagination import HALPaginationSerializer
from drf_hal.serializers import HALModelSerializer
from sample_app.models import Choice, Poll, Channel, Partner


class PollSerializer(HALModelSerializer):
    class Meta:
        model = Poll


class PollWithAdditionalEmbeddedSerializer(HALModelSerializer):
    additional_field = serializers.SerializerMethodField('get_additional_field')

    class Meta:
        model = Poll
        additional_embedded = ('additional_field',)

    def get_additional_field(self, obj):
        return {'value': 'added on %s' % obj.id}


class PollListSerializer(HALPaginationSerializer):
    class Meta:
        model = Poll
        lookup_field = ('pk')


class PollChoiceSerializer(HALModelSerializer):
    class Meta:
        model = Choice
        lookup_field = ('pk', 'poll__pk')
        view_name = 'poll-choice-detail'


class ChoiceSerializer(HALModelSerializer):
    class Meta:
        model = Choice


class ChoiceRelatedSerializer(HALModelSerializer):
    class Meta:
        model = Choice
        exclude = ('poll',)


class CreatePollWithChoicesSerializer(HALModelSerializer):
    choices = ChoiceRelatedSerializer(many=True)

    class Meta:
        model = Poll


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


class ChannelSerializer(HALModelSerializer):

    class Meta:
        model = Channel
        lookup_field = 'pk'


class PartnerSerializer(HALModelSerializer):

    class Meta:
        model = Partner
        lookup_field = 'pk'
