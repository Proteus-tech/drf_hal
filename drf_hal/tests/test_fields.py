# -*- coding: utf-8 -*-
from django.test import TestCase
from drf_hal.fields import HALLinksField


class TestHALLinksField(TestCase):
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
