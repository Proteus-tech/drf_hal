# -*- coding: utf-8 -*-
from drf_hal.serializers import HalModelSerializer
from sample_app.models import Choice


class ChoiceSerializer(HalModelSerializer):
    class Meta:
        model = Choice


class ChoiceExcludePollSerializer(HalModelSerializer):
    class Meta:
        model = Choice
        exclude = ('poll',)


class ChoiceExcludeVotesSerializer(HalModelSerializer):
    class Meta:
        model = Choice
        exclude = ('votes',)
