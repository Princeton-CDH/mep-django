import time
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

from mep.books.models import Item
from mep.books.views import ItemList


class TestBooksViews(TestCase):
    fixtures = ['sample_items']

    def setUp(self):
        self.admin_pass = 'password'
        self.admin_user = get_user_model().objects.create_superuser(
            'admin', 'admin@example.com', self.admin_pass)

    def test_item_autocomplete(self):
        # remove fixture items to duplicate previous test conditions
        Item.objects.all().delete()

        url = reverse('books:item-autocomplete')
        res = self.client.get(url)

        # getting the view returns 200
        assert res.status_code == 200
        data = res.json()
        # there is a results list in the JSON
        assert 'results' in data
        # it is empty because there are no accounts or query
        assert not data['results']

        # - test basic search and sort

        # search by title
        item1 = Item.objects.create(title='Poems Two Painters', mep_id='mep:01',
                                    notes='Author: Knud Merrild')
        item2 = Item.objects.create(title='Collected Poems', mep_id='mep:02')
        res = self.client.get(url, {'q': 'poems'})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 2
        assert data['results'][0]['text'] == item2.title
        assert data['results'][1]['text'] == item1.title

        # search by note text
        res = self.client.get(url, {'q': 'knud'})
        data = res.json()
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == item1.title

        # search by mep id
        res = self.client.get(url, {'q': 'mep:02'})
        data = res.json()
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == item2.title


class TestItemListView(TestCase):
    fixtures = ['sample_items.json', 'multi_creator_item.json']

    def setUp(self):
        # index fixtures and give time for index to take effect
        Item.index_items(Item.objects.all())
        time.sleep(10)
        # bind some convenience items
        self.factory = RequestFactory()
        self.url = reverse('books:books-list')

    def test_list(self):
        response = self.client.get(self.url)

        # should display all items in the database
        items = Item.objects.all()
        assert response.context['items'].count() == items.count()
        self.assertContains(response, '%d total results' % items.count())
        for item in items:
            self.assertContains(response, item.title)
            self.assertContains(response, item.year)
            # NOTE should link to item detail page; not yet implemented
            # self.assertContains(response, item.get_absolute_url())

        # NOTE publishers display is designed but data not yet available

    def test_many_authors(self):
        response = self.client.get(self.url)

        # multi-author item should show first three authors
        novelists = Item.objects.get(pk=4126)
        self.assertContains(response, novelists.authors.first())
        self.assertContains(response, novelists.authors[1])
        self.assertContains(response, novelists.authors[2])

        # other authors should be hidden
        self.assertNotContains(response, novelists.authors[3])

        # should show "...x more authors" text
        self.assertContains(response, '... 16 more authors')

    def test_get_queryset(self):
        # create a mocked form
        view = ItemList()
        form = Mock()
        view.get_form = Mock(return_value=form)
        view.request = self.factory.get(self.url)
        # if form is valid, should return all items sorted by chosen sort
        form.is_valid.return_value = True
        form.cleaned_data = {'sort': 'title'}  # becomes 'title_s'
        solr_qs = view.get_queryset()
        db_qs = Item.objects.order_by('title')
        # querysets from solr and db should match
        for index, item in enumerate(solr_qs):
            assert db_qs[index].title == item['title']
            assert db_qs[index].pk == item['pk']
        # if form is invalid, should return empty queryset
        form.is_valid.return_value = False
        solr_qs = view.get_queryset()
        # NOTE replace with EmptySolrQueryset check when implemented in parasolr
        assert solr_qs.count() == 0

    def test_get_page_labels(self):
        # create a mocked form and some fake items to paginate
        view = ItemList()
        form = Mock()
        view.get_form = Mock(return_value=form)
        view.request = self.factory.get(self.url)
        items = range(120)
        paginator = Paginator(items, per_page=view.paginate_by)
        # if form is valid, should use default implementation (numbered pages)
        # NOTE this will change if we implement alpha pagination for this view
        form.is_valid.return_value = True
        page_labels = view.get_page_labels(paginator)
        assert page_labels == [(1, '1 - 100'), (2, '101 - 120')]
        # if invalid, should return one page with 'N/A' label
        form.is_valid.return_value = False
        page_labels = view.get_page_labels(paginator)
        assert page_labels == [(1, 'N/A')]
