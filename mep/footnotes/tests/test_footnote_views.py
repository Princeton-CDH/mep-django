import time
from types import LambdaType
from unittest.mock import Mock, patch

from django.core.paginator import Paginator
from django.test import RequestFactory, TestCase
from django.urls import reverse

from mep.common.utils import absolutize_url, login_temporarily_required
from mep.footnotes.models import Bibliography, SourceType
from mep.footnotes.views import CardList


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


class TestCardList(TestCase):
    fixtures = ['sample_people', 'sample_cards']

    def setUp(self):
        self.view = CardList()
        self.factory = RequestFactory()
        self.cards_url = reverse('footnotes:cards-list')

    def test_get_absolute_url(self):
        assert self.view.get_absolute_url() == \
            absolutize_url(reverse('footnotes:cards-list'))

    def test_login_required_or_404(self):
        # 404 if not logged in; TEMPORARY
        assert self.client.get(self.cards_url).status_code == 404

    @login_temporarily_required
    @patch('mep.footnotes.views.CardSolrQuerySet')
    def test_get_queryset(self, mock_card_solrqueryset):
        self.view.request = self.factory.get(self.cards_url)
        # simulate fluent interface
        mock_qs = mock_card_solrqueryset.return_value
        for meth in ['facet_field', 'filter', 'only', 'search', 'also',
                     'raw_query_parameters', 'order_by']:
            getattr(mock_qs, meth).return_value = mock_qs

        assert self.view.get_queryset() == mock_card_solrqueryset.return_value
        assert self.view.queryset == mock_card_solrqueryset.return_value

    @login_temporarily_required
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

    @login_temporarily_required
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
