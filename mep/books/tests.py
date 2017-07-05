import re

from django.test import TestCase
from .models import Item, Publisher, PublisherPlace


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
