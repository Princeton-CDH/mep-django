import datetime
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

    def test_authors_editors_translators(self):
        item = Item.objects.create(title='Poems', year=1916)
        author1 = Person.objects.create(name='Smith')
        author2 = Person.objects.create(name='Jones')
        editor = Person.objects.create(name='Ed Mund')
        translator = Person.objects.create(name='Juan Smythe')
        author_type = CreatorType.objects.get(name='Author')
        editor_type = CreatorType.objects.get(name='Editor')
        translator_type = CreatorType.objects.get(name='Translator')

        # add one each of author, editor, and translator
        Creator.objects.create(creator_type=author_type, person=author1,
            item=item)
        Creator.objects.create(creator_type=editor_type, person=editor,
            item=item)
        Creator.objects.create(creator_type=translator_type, person=translator,
            item=item)

        assert len(item.authors) == 1
        assert item.authors.first() == author1
        assert item.author_list() == str(author1)

        # add second author
        Creator.objects.create(creator_type=author_type, person=author2,
            item=item)
        assert len(item.authors) == 2
        assert author1 in item.authors
        assert author2 in item.authors
        assert item.author_list() == '%s; %s' % (author1, author2)

        assert len(item.editors) == 1
        assert item.editors.first() == editor

        assert len(item.translators) == 1
        assert item.translators.first() == translator

    def test_first_known_interaction(self):
        # create a test item with no events
        item = Item.objects.create(title='Searching')
        assert not item.first_known_interaction

        # create a borrow with date
        acct = Account()
        acct.save()
        borrow_date = datetime.date(1940, 3, 2)
        borrow = Borrow(item=item, account=acct)
        borrow.partial_start_date = borrow_date.isoformat()
        borrow.save()
        # first date should be borrow start date
        assert item.first_known_interaction == borrow_date

        # create a borrow with an unknown date
        unknown_borrow = Borrow.objects.create(item=item, account=acct)
        unknown_borrow.partial_start_date = '--01-01'
        unknown_borrow.save()
        # should use previous borrow date, not the unknown (1900)
        assert item.first_known_interaction == borrow_date


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



class TestCreator(TestCase):

    def test_str(self):
        ctype = CreatorType.objects.get(name='Author')
        person = Person.objects.create(name='Joyce')
        item = Item.objects.create(title='Ulysses')
        creator = Creator(creator_type=ctype, person=person, item=item)
        assert str(creator) == ' '.join([str(person), ctype.name, str(item)])