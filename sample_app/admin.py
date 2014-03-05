# -*- coding: utf-8 -*-
from django.contrib import admin
from sample_app.models import Poll, Choice

admin.site.register(Poll)
admin.site.register(Choice)

