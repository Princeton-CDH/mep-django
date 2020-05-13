from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from djiffy.models import Canvas

from mep.people import sitemaps


def test_solr_timestamp_to_date():
    assert sitemaps.solr_timestamp_to_date('2020-05-12T15:46:20.341Z') == \
        date(2020, 5, 12)


class TestMemberSitemap:

    @patch('mep.people.sitemaps.PersonSolrQuerySet')
    def test_items(self, mock_psqs):
        sitemaps.MemberSitemap().items()
        mock_psqs.assert_called_once()
        mock_psqs.return_value.all.assert_called_once()
        mock_psqs.return_value.all.return_value.only \
            .assert_called_with('slug', 'last_modified')

    def test_location(self):
        assert sitemaps.MemberSitemap().location({
            'slug': 'gstein',
            'last_modified': '2020-05-12T15:46:20.341Z'}) == \
            reverse('people:member-detail', args=['gstein'])

    def test_lastmod(self):
        assert sitemaps.MemberSitemap().lastmod({
            'last_modified': '2020-05-12T15:46:20.341Z'}) == \
            date(2020, 5, 12)


class TestMemberCardListSitemap:

    @patch('mep.people.sitemaps.super')
    def test_items(self, mocksuper):
        sitemaps.MemberCardListSitemap().items()
        mocksuper.assert_called_once
        mocksuper.return_value.items.assert_called_once
        mocksuper.return_value.items.return_value \
            .only.assert_called_with('slug', 'last_modified', 'has_card')

    def test_priority(self):
        sitemap = sitemaps.MemberCardListSitemap()
        # has card = default priority
        assert sitemap.priority({'has_card': True}) == sitemap.default_priority
        assert sitemap.priority({'has_card': False}) == sitemap.low_priority


class TestMemberCardDetailSitemap(TestCase):
    fixtures = ['footnotes_gstein', 'sample_people']

    @patch('mep.people.sitemaps.PersonSolrQuerySet')
    def test_items(self, mock_psqs):
        mock_psqs.return_value.filter.return_value.only.return_value \
            .get_results.return_value = [{
                'slug': 'stein-gertrude',
                'last_modified': '2020-05-12T15:46:20.341Z'}
            ]

        sitemap = sitemaps.MemberCardDetailSitemap()
        items = sitemap.items()
        # all the canvas objects associated wiht an account should be listed;
        # all fixture canvas objects associated with with gertrude stein
        canvas_ids = Canvas.objects \
            .filter(manifest__bibliography__account__isnull=False) \
            .values_list('short_id', flat=True)
        assert len(items) == len(canvas_ids)
        for obj in items:
            assert obj['short_id'] in canvas_ids
            assert obj['slug'] == 'stein-gertrude'

        # solr queried
        mock_psqs.assert_called_once()
        mock_psqs.return_value.filter.assert_called_with(has_card=True)
        mock_psqs.return_value.filter.return_value.only \
            .assert_called_with('slug', 'last_modified')

        # lastmodified lookup populated
        assert sitemap.members_lastmod
        assert sitemap.members_lastmod['stein-gertrude'] == date(2020, 5, 12)

    def test_location(self):
        obj = {
            'slug': 'gstein',
            'short_id': '9242203d-d33e',
        }
        assert sitemaps.MemberCardDetailSitemap().location(obj) == \
            reverse('people:member-card-detail',
                    args=['gstein', obj['short_id']])
