import re

from django.test import TestCase

from mep.accounts.models import Borrow, Account
from mep.books.models import Item, Publisher, PublisherPlace, Creator, \
    CreatorType
from mep.people.models import Person


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

    def test_authors(self):
        item = Item.objects.create(title='Poems', year=1916)
        author1 = Person.objects.create(name='Smith')
        author2 = Person.objects.create(name='Jones')
        editor = Person.objects.create(name='Ed Mund')
        author_type = CreatorType.objects.get(name='Author')
        editor_type = CreatorType.objects.get(name='Editor')

        # add single author and editor
        Creator.objects.create(creator_type=author_type, person=author1,
            item=item)
        Creator.objects.create(creator_type=editor_type, person=editor,
            item=item)

        assert len(item.authors) == 1
        assert item.authors[0] == author1
        assert item.author_list() == str(author1)

        # add second author
        Creator.objects.create(creator_type=author_type, person=author2,
            item=item)
        assert len(item.authors) == 2
        assert author1 in item.authors
        assert author2 in item.authors
        assert item.author_list() == '%s, %s' % (author1, author2)



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