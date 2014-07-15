# -*- coding: utf-8 -*-
from rest_framework.renderers import JSONRenderer


class HALRenderer(JSONRenderer):
    media_type = 'application/hal+json'

