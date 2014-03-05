# -*- coding: utf-8 -*-
from drf_hal.serializers import HalModelSerializer
from sample_app.models import Choice


class ChoiceSerializer(HalModelSerializer):
    class Meta:
        model = Choice
