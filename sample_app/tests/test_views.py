# -*- coding: utf-8 -*-
from datetime import date

from django.core.urlresolvers import reverse
from django.test import TestCase
import simplejson
from dougrain import Document

from sample_app.models import Poll, Choice, Partner, Channel


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

    def test_get_choice_with_fields(self):
        response = self.client.get('/choice/%s?fields=true' % self.choice.id)
        self.assertEqual(response.status_code, 200)

    def test_get_choice_with_lookup_field(self):
        response = self.client.get('/choice/%s?lookup_field=true' % self.choice.id)
        self.assertEqual(response.status_code, 200)

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


class TestPollWithAdditionEmbeddedView(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(question='What is your favorite food?', pub_date=date(2014, 1, 3))

    def test_get_with_additional_embedded_view(self):
        response = self.client.get('/poll_with_additional_embedded/%s' % self.poll.id)
        self.assertEqual(response.status_code, 200)

        content = simplejson.loads(response.content)
        doc = Document.from_object(content)
        self.assertEqual(doc.links['self'].url(), 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(doc.embedded['additional_field'].properties['value'], 'added on %s' % self.poll.id)


class TestPollChoiceView(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(question='What is your favorite food?', pub_date=date(2014, 1, 3))
        self.choice = Choice.objects.create(poll=self.poll, choice_text='Sushi')

    def test_get_poll_choice_view(self):
        response = self.client.get('/poll/%s/choice/%s' % (self.poll.id, self.choice.id))
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        doc = Document.from_object(content)
        self.assertEqual(doc.links['self'].url(), 'http://testserver/poll/%s/choice/%s' % (self.poll.id, self.choice.id))
        self.assertEqual(doc.links['poll'].url(), 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(doc.properties['choice_text'], self.choice.choice_text)
        self.assertEqual(doc.properties['votes'], 0)
        self.assertNotIn('poll', doc.properties)

    def test_get_poll_choice_view_returns_404_if_all_the_lookup_fields_do_not_match(self):
        poll = Poll.objects.create(question='What is your favorite color?', pub_date=date(2014, 1, 3))
        response = self.client.get('/poll/%s/choice/%s' % (poll.id, self.choice.id))
        self.assertEqual(response.status_code, 404)


class TestCreatePollChoiceView(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(question='What is your favorite food?', pub_date=date(2014, 1, 3))

    def test_create_poll_choice_successfully(self):
        data = {
            'choice_text': 'Oishi'
        }
        response = self.client.post('/poll/%s/choice' % self.poll.id, data=simplejson.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        choice = Choice.objects.get(poll=self.poll, choice_text=data['choice_text'])
        content = simplejson.loads(response.content)
        doc = Document.from_object(content)
        self.assertEqual(doc.links['self'].url(), 'http://testserver/poll/%s/choice/%s' % (self.poll.id, choice.id))
        self.assertEqual(doc.links['poll'].url(), 'http://testserver/poll/%s' % self.poll.id)
        self.assertEqual(doc.properties['choice_text'], choice.choice_text)
        self.assertEqual(doc.properties['votes'], 0)
        self.assertNotIn('poll', doc.properties)


class TestPollListView(TestCase):
    def __create_polls(self, count):
        for index in xrange(0, count):
            Poll.objects.create(question='Poll%s' % index, pub_date=date(2014, 8, 8))

    def test_get_poll_list(self):
        self.__create_polls(30)

        response = self.client.get('/polls')
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        _links = content['_links']
        _embedded = content['_embedded']
        self.assertEqual(content['total'], 30)
        self.assertEqual(content['num_pages'], 3)
        self.assertEqual(_links['self']['href'], 'http://testserver/polls')
        self.assertEqual(_links['first']['href'], 'http://testserver/polls?page=1')
        self.assertEqual(_links['last']['href'], 'http://testserver/polls?page=3')
        self.assertEqual(_links['next']['href'], 'http://testserver/polls?page=2')
        self.assertIsNone(_links['prev'])

    def test_get_poll_list_no_page(self):
        response = self.client.get('/polls')
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        _links = content['_links']
        _embedded = content['_embedded']
        self.assertEqual(content['total'], 0)
        self.assertEqual(content['num_pages'], 1)
        self.assertEqual(_links['self']['href'], 'http://testserver/polls')
        self.assertIsNone(_links['first'])
        self.assertIsNone(_links['last'])
        self.assertIsNone(_links['next'])
        self.assertIsNone(_links['prev'])

    def test_get_poll_list_only_one_page(self):
        self.__create_polls(10)

        response = self.client.get('/polls')
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        _links = content['_links']
        _embedded = content['_embedded']
        self.assertEqual(content['total'], 10)
        self.assertEqual(content['num_pages'], 1)
        self.assertEqual(_links['self']['href'], 'http://testserver/polls')
        self.assertEqual(_links['first']['href'], 'http://testserver/polls?page=1')
        self.assertEqual(_links['last']['href'], 'http://testserver/polls?page=1')
        self.assertIsNone(_links['next'])
        self.assertIsNone(_links['prev'])

    def test_get_poll_list_at_last_page_no_next_page(self):
        self.__create_polls(20)

        response = self.client.get('/polls?page=2')
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        _links = content['_links']
        _embedded = content['_embedded']
        self.assertEqual(content['total'], 20)
        self.assertEqual(content['num_pages'], 2)
        self.assertEqual(_links['self']['href'], 'http://testserver/polls?page=2')
        self.assertEqual(_links['first']['href'], 'http://testserver/polls?page=1')
        self.assertEqual(_links['last']['href'], 'http://testserver/polls?page=2')
        self.assertIsNone(_links['next'])
        self.assertEqual(_links['prev']['href'], 'http://testserver/polls?page=1')

    def test_get_poll_list_has_both_prev_and_next_page(self):
        self.__create_polls(40)

        response = self.client.get('/polls?page=3')
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        _links = content['_links']
        _embedded = content['_embedded']
        self.assertEqual(content['total'], 40)
        self.assertEqual(content['num_pages'], 4)
        self.assertEqual(_links['self']['href'], 'http://testserver/polls?page=3')
        self.assertEqual(_links['first']['href'], 'http://testserver/polls?page=1')
        self.assertEqual(_links['last']['href'], 'http://testserver/polls?page=4')
        self.assertEqual(_links['next']['href'], 'http://testserver/polls?page=4')
        self.assertEqual(_links['prev']['href'], 'http://testserver/polls?page=2')

    def test_get_poll_list_return_count_for_the_page(self):
        self.__create_polls(10)

        response = self.client.get('/polls?page_size=3')
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        _links = content['_links']
        _embedded = content['_embedded']
        self.assertEqual(content['total'], 10)
        self.assertEqual(content['num_pages'], 4)
        self.assertEqual(content['count'], 3)


class TestCreatePollAPIView(TestCase):
    def setUp(self):
        self.data = dict(
            question='What is your favorite animal?',
            pub_date='2014-03-01T00:00:00Z',
            choices=[
                {
                    'choice_text': 'cat',
                },
                {
                    'choice_text': 'dog'
                }
            ]
        )
        self.test_uri = '/poll_with_choices'

    def test_create_poll_with_choices_successful(self):
        response = self.client.post(self.test_uri, simplejson.dumps(self.data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        poll = Poll.objects.get(question=self.data['question'])
        choices = Choice.objects.filter(poll=poll)
        self.assertEqual(choices.count(), 2)
        self.assertEqual(choices[0].choice_text, self.data['_embedded']['choices'][0]['choice_text'])
        self.assertEqual(choices[1].choice_text, self.data['_embedded']['choices'][1]['choice_text'])

    def test_create_poll_with_choices_no_choice(self):
        del self.data['choices']
        response = self.client.post(self.test_uri, simplejson.dumps(self.data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        content = simplejson.loads(response.content)
        print content
        self.assertEqual(content['choices'], ["This field is required."])


class TestCreateChannelAPIView(TestCase):
    def setUp(self):
        self.partner = Partner.objects.create(name='abc')
        self.partner_uri = 'http://testserver%s' % reverse('partner-detail', kwargs={'pk': self.partner.pk})

        self.data = {
            'partners': [self.partner_uri],
            'name': 'ABC'
        }
        self.test_uri = reverse('create-channel')

    def test_create_channel(self):
        response = self.client.post(self.test_uri, simplejson.dumps(self.data), content_type='application/json')
        self.assertEqual(response.status_code, 201)

        saved_channel = Channel.objects.get(name=self.data['name'])

        content = simplejson.loads(response.content)
        _links = content['_links']
        self.assertDictEqual(_links['self'], {'href': 'http://testserver%s' % reverse('channel-detail',
                                                                                     kwargs={'pk': saved_channel.pk})})
        self.assertEqual(_links['partners'], [{'href': self.partner_uri}])
        self.assertEqual(content['name'], saved_channel.name)
