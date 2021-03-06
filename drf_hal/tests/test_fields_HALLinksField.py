# -*- coding: utf-8 -*-
import warnings
from django.core.urlresolvers import NoReverseMatch
from django.http import HttpRequest
from django.test import TestCase
from mock import Mock, patch
from rest_framework.request import Request
from drf_hal.fields import HALLinksField


class TestHALLinksFieldInitialization(TestCase):
    def setUp(self):
        self.additional_links = {'choices': object()}
        self.exclude = ('poll',)
        self.links_format = 'xml'

    def test_initialization_basic(self):
        links_field = HALLinksField(
            view_name='poll-detail',
            additional_links=self.additional_links,
            exclude=self.exclude,
            format=self.links_format
        )
        self.assertEqual(links_field.additional_links, self.additional_links)
        self.assertEqual(links_field.exclude, self.exclude)
        self.assertEqual(links_field.format, self.links_format)
        self.assertEqual(links_field.lookup_field, 'pk')

    def test_initialization_with_lookup_field(self):
        links_field = HALLinksField(
            view_name='poll-detail',
            additional_links=self.additional_links,
            exclude=self.exclude,
            format=self.links_format,
            lookup_field='slug'
        )
        self.assertEqual(links_field.additional_links, self.additional_links)
        self.assertEqual(links_field.exclude, self.exclude)
        self.assertEqual(links_field.format, self.links_format)
        self.assertEqual(links_field.lookup_field, 'slug')

    def test_initialization_throw_error_if_there_is_no_view_name(self):
        with self.assertRaisesRegexp(ValueError, "requires 'view_name'"):
            HALLinksField(
                additional_links=self.additional_links,
                exclude=self.exclude,
                format=self.links_format,
            )


class TestHALLinksFieldFieldToNative(TestCase):
    def setUp(self):
        self.view_name = 'poll-detail'
        self.links_format = 'xml'

        self.links_field = HALLinksField(
            view_name=self.view_name,
            format=self.links_format
        )

        self.links_field.get_url = Mock()
        self.self_link = 'http://about/me'
        self.links_field.get_url.return_value = self.self_link
        self.links_field.context = dict()
        self.request = Request(HttpRequest())
        self.links_field.context['request'] = self.request
        self.links_field.context['format'] = self.links_format

        self.obj = Mock()

    def test_field_to_native(self):
        ret = self.links_field.field_to_native(self.obj, 'vote_number')

        expected_ret = {
            'self': {
                'href': self.self_link
            }
        }
        self.assertDictEqual(ret, expected_ret)

    def test_field_to_native_no_request_has_warning(self):
        del self.links_field.context['request']
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")

            self.links_field.field_to_native(self.obj, 'vote_number')

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, RuntimeWarning))
            self.assertIn("not allowed", str(w[-1].message))

    def test_field_to_native_different_format_in_context_and_when_initialized(self):
        self.links_field.context['format'] = 'json'

        self.links_field.field_to_native(self.obj, 'vote_number')

        self.links_field.get_url.assert_called_once_with(self.obj, self.view_name, self.request, self.links_format)

    def test_field_to_native_no_reverse_match(self):
        self.links_field.get_url.side_effect = NoReverseMatch

        with self.assertRaisesRegexp(Exception, 'Could not resolve URL'):
            self.links_field.field_to_native(self.obj, 'vote_number')


class TestHALLinksFieldGetUrl(TestCase):
    def setUp(self):
        self.patch_reverse = patch('rest_framework.reverse.reverse')
        self.mock_reverse = self.patch_reverse.start()

        self.view_name = 'poll-detail'
        self.links_format = 'xml'

        self.links_field = HALLinksField(
            view_name=self.view_name,
            format=self.links_format
        )

        self.obj = Mock()
        self.request = Request(HttpRequest())

    def tearDown(self):
        self.patch_reverse.stop()

    def test_get_url_successful(self):
        expected_url =  'http://yeah/url'
        self.mock_reverse.return_value = expected_url

        url = self.links_field.get_url(self.obj, self.view_name, self.request, 'json')

        self.assertEqual(url, expected_url)

    def test_get_url_cannot_get_lookup_field(self):
        self.obj.pk = None

        url = self.links_field.get_url(self.obj, self.view_name, self.request, 'json')

        self.assertIsNone(url)

    def test_get_url_no_reverse_match(self):
        self.mock_reverse.side_effect = NoReverseMatch

        with self.assertRaises(NoReverseMatch):
            url = self.links_field.get_url(self.obj, self.view_name, self.request, 'json')


