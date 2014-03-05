# -*- coding: utf-8 -*-
from datetime import date
from django.test import TestCase
from sample_app.models import Poll, Choice


class TestChoiceView(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(question='What is your favorite food?', pub_date=date(2014, 1, 3))

    def test_get_choice(self):
        choice = Choice.objects.create(poll=self.poll, choice_text='Sushi')
        response = self.client.get('/choice/%s' % choice.id)
        self.assertEqual(response.status_code, 200)

