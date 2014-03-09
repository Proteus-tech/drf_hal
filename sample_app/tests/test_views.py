# -*- coding: utf-8 -*-
from datetime import date
from django.test import TestCase
import simplejson
from sample_app.models import Poll, Choice


class TestChoiceView(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(question='What is your favorite food?', pub_date=date(2014, 1, 3))
        self.choice = Choice.objects.create(poll=self.poll, choice_text='Sushi')

    def test_get_choice(self):
        response = self.client.get('/choice/%s' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        self.assertEqual(content['_links']['self']['href'], 'http://testserver/choice/%s' % self.choice.id)
        self.assertEqual(content['_links']['poll']['href'], 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(content['choice_text'], self.choice.choice_text)
        self.assertEqual(content['votes'], self.choice.votes)

    def test_get_choice_exclude_poll(self):
        response = self.client.get('/choice/%s?exclude=poll' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        self.assertEqual(content['_links']['self']['href'], 'http://testserver/choice/%s' % self.choice.id)
        self.assertEqual(content['choice_text'], self.choice.choice_text)
        self.assertEqual(content['votes'], self.choice.votes)
        self.assertNotIn('poll', content['_links'])

    def test_get_choice_exclude_votes(self):
        response = self.client.get('/choice/%s?exclude=votes' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        self.assertEqual(content['_links']['self']['href'], 'http://testserver/choice/%s' % self.choice.id)
        self.assertEqual(content['_links']['poll']['href'], 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(content['choice_text'], self.choice.choice_text)
        self.assertNotIn('votes', content)

    def test_get_choice_embed_poll(self):
        response = self.client.get('/choice/%s?embed=poll' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        self.assertEqual(content['_links']['self']['href'], 'http://testserver/choice/%s' % self.choice.id)
        self.assertEqual(content['choice_text'], self.choice.choice_text)
        self.assertEqual(content['votes'], self.choice.votes)
        self.assertEqual(content['_embedded']['poll']['question'], self.poll.question)
        # self.assertEqual(content['_embedded']['poll']['pub_date'], self.poll.pub_date.isoformat())
        self.assertEqual(content['_embedded']['poll']['_links']['self']['href'], 'http://testserver/poll/%s' % self.poll.id)
        self.assertNotIn('poll', content['_links'])

    def test_get_choice_extra_link(self):
        response = self.client.get('/choice/%s?extra_link=create' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        self.assertEqual(content['_links']['self']['href'], 'http://testserver/choice/%s' % self.choice.id)
        self.assertEqual(content['_links']['poll']['href'], 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(content['_links']['create']['href'], 'http://testserver/choice')
        self.assertEqual(content['choice_text'], self.choice.choice_text)
        self.assertEqual(content['votes'], self.choice.votes)

