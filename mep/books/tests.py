import re

from django.test import TestCase
from django.urls import reverse
from mep.books.models import Item, Publisher, PublisherPlace


class TestItem(TestCase):

    def test_repr(self):
        item = Item(title='Le foo et le bar', year=1916)
        overall = re.compile(r"<Item \{.+\}>")
        assert re.search(overall, repr(item))

    def test_str(self):

        # Test pattern for title and year
        item = Item(title='Le foo et le bar', year=1916)
        assert str(item) == 'Le foo et le bar (1916)'
        # Test pattern for just title
        item.year = None
        assert str(item) == 'Le foo et le bar'
        # Test pattern for no title or year
        item.title = ''
        assert str(item) == '(No title, year)'


class TestPublisher(TestCase):

    def test_repr(self):
        publisher = Publisher(name='Foo, Bar, and Co.')
        overall = re.compile(r"<Publisher \{.+\}>")
        assert re.search(overall, repr(publisher))

    def test_str(self):
        publisher = Publisher(name='Foo, Bar, and Co.')
        assert str(publisher) == 'Foo, Bar, and Co.'


class TestPublisherPlace(TestCase):

    def test_repr(self):
        pub_place = PublisherPlace(name='London', latitude=23, longitude=45)
        overall = re.compile(r"<PublisherPlace \{.+\}>")
        assert re.search(overall, repr(pub_place))

    def test_str(self):
        pub_place = PublisherPlace(name='London', latitude=23, longitude=45)
        assert str(pub_place) == 'London'


class TestBooksViews(TestCase):

    def test_item_autocomplete(self):
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

