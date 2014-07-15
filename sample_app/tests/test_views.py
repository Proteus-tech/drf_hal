# -*- coding: utf-8 -*-
from datetime import date
from django.test import TestCase
import simplejson
from dougrain import Document
from sample_app.models import Poll, Choice


class TestChoiceView(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(question='What is your favorite food?', pub_date=date(2014, 1, 3))
        self.choice = Choice.objects.create(poll=self.poll, choice_text='Sushi')

    def test_get_choice(self):
        response = self.client.get('/choice/%s' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        doc = Document.from_object(content)
        self.assertEqual(doc.links['self'].url(), 'http://testserver/choice/%s' % self.choice.id)
        self.assertEqual(doc.links['poll'].url(), 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(doc.properties['choice_text'], self.choice.choice_text)
        self.assertEqual(doc.properties['votes'], self.choice.votes)

    def test_get_choice_exclude_poll(self):
        response = self.client.get('/choice/%s?exclude=poll' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        doc = Document.from_object(content)
        self.assertEqual(doc.links['self'].url(), 'http://testserver/choice/%s' % self.choice.id)
        self.assertNotIn('poll', doc.links)
        self.assertEqual(doc.properties['choice_text'], self.choice.choice_text)
        self.assertEqual(doc.properties['votes'], self.choice.votes)

    def test_get_choice_exclude_votes(self):
        response = self.client.get('/choice/%s?exclude=votes' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        doc = Document.from_object(content)
        self.assertEqual(doc.links['self'].url(), 'http://testserver/choice/%s' % self.choice.id)
        self.assertEqual(doc.links['poll'].url(), 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(doc.properties['choice_text'], self.choice.choice_text)
        self.assertNotIn('votes', doc.properties)

    def test_get_choice_embed_poll(self):
        response = self.client.get('/choice/%s?embed=poll' % self.choice.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        doc = Document.from_object(content)
        self.assertEqual(doc.links['self'].url(), 'http://testserver/choice/%s' % self.choice.id)
        self.assertNotIn('poll', doc.links)
        self.assertEqual(doc.embedded['poll'].properties['question'], self.poll.question)
        self.assertEqual(doc.embedded['poll'].url(), 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(doc.properties['choice_text'], self.choice.choice_text)
        self.assertEqual(doc.properties['votes'], self.choice.votes)

    def test_get_choice_view_has_json_hal_content_type(self):
        response = self.client.get('/choice/%s' % self.choice.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/hal+json')


class TestPollView(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(question='What is your favorite food?', pub_date=date(2014, 1, 3))

    def test_get_poll_view(self):
        response = self.client.get('/poll/%s' % self.poll.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        doc = Document.from_object(content)
        self.assertEqual(doc.links['self'].url(), 'http://testserver/poll/%s' % self.poll.id)

