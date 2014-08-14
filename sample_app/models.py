# -*- coding: utf-8 -*-

from django.db import models


class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')


class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


class Partner(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=False, null=False)


class Channel(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=False, null=False)
    partner = models.ManyToManyField(Partner, null=True)
