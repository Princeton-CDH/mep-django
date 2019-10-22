from types import LambdaType
from datetime import date
import time
from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.test import TestCase, RequestFactory
from django.urls import reverse
from djiffy.models import Manifest

from mep.accounts.models import Account, Event
from mep.common.utils import absolutize_url, login_temporarily_required
from mep.footnotes.admin import BibliographyAdmin
from mep.footnotes.models import Bibliography, Footnote, SourceType
from mep.footnotes.views import CardList
from mep.people.models import Person


class TestSourceType(TestCase):

    def test_item_count(self):
        src_type = SourceType.objects.create(name='website')
        assert src_type.item_count() == 0

        Bibliography.objects.create(bibliographic_note='citation',
                                    source_type=src_type)
        assert src_type.item_count() == 1


class TestBibliography(TestCase):

    def test_str(self):
        src_type = SourceType.objects.create(name='website')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
                                           source_type=src_type)
        assert str(bibl) == 'citation'

    def test_footnote_count(self):
        src_type = SourceType.objects.create(name='website')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
                                           source_type=src_type)
        assert bibl.footnote_count() == 0

        # find an arbitrary content type to attach a footnote to
        content_type = ContentType.objects.first()
        Footnote.objects.create(bibliography=bibl, content_type=content_type,
                                object_id=1, is_agree=False)
        assert bibl.footnote_count() == 1

    def test_items_to_index(self):
        with patch.object(Bibliography.objects, 'filter') as \
                mock_bib_filter:
            Bibliography.items_to_index()
            mock_bib_filter.assert_called_with(account__isnull=False,
                                               manifest__isnull=False)

    def test_index_data(self):
        src_type = SourceType.objects.create(name='Lending Library Card')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
                                           source_type=src_type)
        # no account or manifest, no index data
        index_data = bibl.index_data()
        assert 'item_type' not in index_data
        assert len(index_data.keys()) == 1
        # account but no manifest, no index data
        acct = Account.objects.create(card=bibl)
        assert 'item_type' not in bibl.index_data()

        bibl.manifest = Manifest()
        with patch.object(Manifest, 'thumbnail') as mock_thumbnail:
            test_iiif_img_url = 'iiif.image.url'
            mock_thumbnail.image.size.return_value = test_iiif_img_url
            index_data = bibl.index_data()
            assert index_data['thumbnail_t'] == test_iiif_img_url
            assert index_data['thumbnail2x_t'] == test_iiif_img_url
            mock_thumbnail.image.size.assert_any_call(width=225)
            mock_thumbnail.image.size.assert_any_call(width=225 * 2)

            # add people and events to account
            leon = Person.objects.create(sort_name='Edel, Leon')
            bertha = Person.objects.create(sort_name='Edel, Bertha')
            acct.persons.add(leon)
            acct.persons.add(bertha)
            Event.objects.create(account=acct, start_date=date(1919, 11, 17))
            Event.objects.create(account=acct, start_date=date(1922, 1, 15))
            Event.objects.create(account=acct, start_date=date(1936, 5, 3))
            index_data = bibl.index_data()

            assert leon.sort_name in index_data['cardholder_t']
            assert bertha.sort_name in index_data['cardholder_t']
            assert index_data['cardholder_sort_s'] == bertha.sort_name
            for year in (1919, 1922, 1936):
                assert year in index_data['years_is']
            assert index_data['start_i'] == 1919
            assert index_data['end_i'] == 1936


class TestFootnote(TestCase):

    def test_str(self):
        src_type = SourceType.objects.create(name='website')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
                                           source_type=src_type)
        # find an arbitrary content type to attach a footnote to
        content_type = ContentType.objects.first()
        fn = Footnote.objects.create(bibliography=bibl, content_type=content_type,
                                     object_id=1, is_agree=False)

        assert 'Footnote on %s' % fn.content_object in str(fn)

        assert '(%s)' % bibl in str(fn)
        fn.location = 'http://so.me/url/'
        assert '(%s %s)' % (bibl, fn.location) in str(fn)

    def test_image_thumbnail(self):
        fnote = Footnote()
        # no image - returns none, but does not error
        assert not fnote.image_thumbnail()

        # image but no rendering
        with patch.object(Footnote, 'image') as mockimage:
            img = '<img/>'
            mockimage.manifest.extra_data = {}
            mockimage.admin_thumbnail.return_value = img
            assert fnote.image_thumbnail() == img

            test_rendering_url = 'http://img.co/url'
            mockimage.manifest.extra_data = {
                'rendering': {'@id': test_rendering_url}
            }
            image_thumbnail = fnote.image_thumbnail()
            assert img in image_thumbnail
            assert image_thumbnail.startswith(
                '<a target="_blank" href="%s">' % test_rendering_url
            )


class TestBibliographyAutocomplete(TestCase):

    def test_bibliography_autocomplete(self):

        url = reverse('footnotes:bibliography-autocomplete')
        res = self.client.get(url)

        # getting the view returns 200
        assert res.status_code == 200
        data = res.json()
        # there is a results list in the JSON
        assert 'results' in data
        # it is empty because there are no accounts or query
        assert not data['results']

        # - test search and sort
        source_type = SourceType.objects.create(name='card')
        bib1 = Bibliography.objects.create(
            source_type=source_type,
            bibliographic_note='Found in a box with some foobars.'
        )
        bib2 = Bibliography.objects.create(
            source_type=source_type,
            bibliographic_note='The private collection of Mr. Baz'
        )
        # return all
        res = self.client.get(url)
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 2
        assert data['results'][0]['text'] == str(bib1)

        # return one based on search
        data = self.client.get(url, {'q': 'baz'}).json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == str(bib2)


class TestBibliographyAdmin:

    def test_manifest_thumbnail(self):
        bibadmin = BibliographyAdmin(Mock(), Mock())

        # no manifest, no error
        obj = Mock(manifest=None)
        img = bibadmin.manifest_thumbnail(obj)
        assert not img

        # manifest, no rendering
        obj.manifest = Mock(extra_data={})
        img = '<img/>'
        obj.manifest.admin_thumbnail.return_value = img
        assert bibadmin.manifest_thumbnail(obj) == img

        test_rendering_url = 'http://img.co/url'
        obj.manifest.extra_data = {
            'rendering': {'@id': test_rendering_url}
        }
        manifest_thumbnail = bibadmin.manifest_thumbnail(obj)
        assert img in manifest_thumbnail
        assert manifest_thumbnail.startswith(
            '<a target="_blank" href="%s">' % test_rendering_url
        )


class TestCardList(TestCase):
    fixtures = ['sample_people', 'sample_cards']

    def setUp(self):
        self.view = CardList()
        self.factory = RequestFactory()
        self.cards_url = reverse('footnotes:card-list')

    def test_login_required_or_404(self):
        # 404 if not logged in; TEMPORARY
        assert self.client.get(self.cards_url).status_code == 404

    def test_get_absolute_url(self):
        assert self.view.get_absolute_url() == \
            absolutize_url(reverse('footnotes:card-list'))

    @patch('mep.footnotes.views.CardSolrQuerySet')
    def test_get_queryset(self, mock_card_solrqueryset):
        assert self.view.get_queryset() == mock_card_solrqueryset.return_value
        assert self.view.queryset == mock_card_solrqueryset.return_value

    def test_get_breadcrumbs(self):
        crumbs = self.view.get_breadcrumbs()
        assert crumbs[0][0] == 'Home'
        # last item is this page
        assert crumbs[1][0] == 'Cards'
        assert crumbs[1][1] == self.view.get_absolute_url()

    @login_temporarily_required
    def test_list(self):
        # test listview functionality using testclient & response

        # index cards in solr
        Bibliography.index_items(Bibliography.items_to_index())
        time.sleep(1)

        response = self.client.get(self.cards_url)

        # filter form should be displayed with filled-in query field one time
        # NOTE: disabled for now
        # self.assertContains(
        #    response, 'Search by library member', count=1)

        # should display all cards in the fixture
        cards = Bibliography.items_to_index()

        assert response.context['cards'].count() == cards.count()
        self.assertContains(response, 'Displaying %d results' % cards.count())
        for card in cards:
            self.assertContains(
                response, card.account_set.first().persons.first().sort_name)
            # 1x image appears twice (src + srcset)
            self.assertContains(
                response,
                card.manifest.thumbnail.image.size(width=225), count=2)
            # 2x image appears once
            self.assertContains(
                response,
                card.manifest.thumbnail.image.size(width=225 * 2), count=1)
            # one fixture has dates, one does not
            card_years = card.account_set.first().event_dates
            if card_years:
                self.assertContains(response, min(card_years).year)
                self.assertContains(response, max(card_years).year)
            else:
                self.assertContains(response, 'Unknown')

    def test_get_page_labels(self):
        view = CardList()
        view.request = self.factory.get(self.cards_url)
        # trigger form valid check to ensure cleaned data is available
        view.get_form().is_valid()
        view.queryset = Mock()
        with patch('mep.footnotes.views.alpha_pagelabels') as \
                mock_alpha_pglabels:
            works = range(101)
            paginator = Paginator(works, per_page=50)
            result = view.get_page_labels(paginator)
            view.queryset.only.assert_called_with('cardholder_sort')
            alpha_pagelabels_args = mock_alpha_pglabels.call_args[0]
            # first arg is paginator
            assert alpha_pagelabels_args[0] == paginator
            # second arg is queryset with revised field list
            assert alpha_pagelabels_args[1] == view.queryset.only.return_value
            # third arg is a lambda
            assert isinstance(alpha_pagelabels_args[2], LambdaType)

            mock_alpha_pglabels.return_value.items.assert_called_with()
            assert result == mock_alpha_pglabels.return_value \
                                                .items.return_value

            # No keyword search for now
            # # when sorting by relevance, use numeric page labels instead
            # mock_alpha_pglabels.reset_mock()
            # view.request = self.factory.get(self.cards_url, {'query': 'foo'})
            # del view._form
            # # trigger form valid check to ensure cleaned data is available
            # view.get_form().is_valid()
            # result = view.get_page_labels(paginator)
            # mock_alpha_pglabels.assert_not_called()
