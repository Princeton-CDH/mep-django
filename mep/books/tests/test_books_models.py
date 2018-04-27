import re

from django.test import TestCase
from mep.books.models import Item, Publisher, PublisherPlace
from mep.accounts.models import Borrow, Account


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

    def test_borrow_count(self):

        # create a test item
        # should have zero borrows
        item = Item(title='Le foo et le bar', year=1916)
        item.save()
        assert item.borrow_count == 0
        # create a test account and borrow the item once
        # should have one borrow
        acct = Account()
        acct.save()
        Borrow(item=item, account=acct).save()
        # borrow a few more times and test the count
        Borrow(item=item, account=acct).save()
        Borrow(item=item, account=acct).save()
        Borrow(item=item, account=acct).save()
        assert item.borrow_count == 4


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