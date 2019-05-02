import datetime
import os
import re
from unittest.mock import Mock, patch

from django.test import TestCase
import requests

from mep.accounts.models import Borrow, Account
from mep.books.models import Item, Publisher, PublisherPlace, Creator, \
    CreatorType, Subject
from mep.books.tests.test_oclc import FIXTURE_DIR
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

    @patch('mep.books.models.Subject.create_from_uri')
    def test_populate_from_worldcat(self, mock_create_from_uri):
        item = Item.objects.create(title='Time and Tide')
        worldcat_entity = Mock(
            work_uri='http://worldcat.org/entity/work/id/3372107206',
            item_uri='http://www.worldcat.org/oclc/3484871',
            genre='Periodicals',
            item_type='http://schema.org/Periodical',
            subjects=[]
        )
        item.populate_from_worldcat(worldcat_entity)
        assert item.uri == worldcat_entity.work_uri
        assert item.edition_uri == worldcat_entity.item_uri
        assert item.genre == worldcat_entity.genre
        assert item.item_type == worldcat_entity.item_type
        # no subjects on the eentity
        assert not item.subjects.all()

        worldcat_entity.subjects = [
            'http://viaf.org/viaf/97006051',
            'http://id.worldcat.org/fast/1259831/'
        ]

        # create test subjects for mock so we can create
        # them on-demand and test them not existing prior
        def make_test_subject(uri):
            if 'viaf' in uri:
                return Subject.objects.create(
                    uri=uri, name='Ernest Hemingway',
                    rdf_type='http://schema.org/Person')

            return Subject.objects.create(
                uri=uri, name='Lorton, Virginia',
                rdf_type='http://schema.org/Place')

        mock_create_from_uri.side_effect = make_test_subject
        item.populate_from_worldcat(worldcat_entity)
        assert item.subjects.count() == 2
        assert mock_create_from_uri.call_count == 2
        mock_create_from_uri.assert_any_call(worldcat_entity.subjects[0])
        mock_create_from_uri.assert_any_call(worldcat_entity.subjects[1])

        # if the subjects already exist, they should not be created
        mock_create_from_uri.reset_mock()
        item.populate_from_worldcat(worldcat_entity)
        mock_create_from_uri.assert_not_called()
        assert item.subjects.count() == 2

        # test replaces previous subjects
        del worldcat_entity.subjects[-1]
        item.populate_from_worldcat(worldcat_entity)
        assert item.subjects.count() == 1

        # simulate error creating subject
        worldcat_entity.subjects = [
            'http://example.com/about/me',
        ]
        mock_create_from_uri.side_effect = requests.exceptions.HTTPError
        # shouldn't error
        item.populate_from_worldcat(worldcat_entity)
        mock_create_from_uri.assert_called_with(worldcat_entity.subjects[0])
        # should set to subjects it could find/create (in this case, none)
        assert not item.subjects.count()

    def test_subject_list(self):
        # no subjects
        item = Item.objects.create(title='Topicless')
        assert item.subject_list() == ''

        subj1 = Subject.objects.create(
            uri='http://viaf.org/viaf/97006051', name='Ernest Hemingway',
            rdf_type='http://schema.org/Person')
        subj2 = Subject.objects.create(
            uri='http://id.worldcat.org/fast/1259831/',
            name='Lorton, Virginia', rdf_type='http://schema.org/Place')
        item.subjects.add(subj1)
        item.subjects.add(subj2)
        assert item.subject_list() == '%s; %s' % (subj1.name, subj2.name)


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


class TestSubject(TestCase):

    def get_test_subject(self):
        return Subject(
            name='Mark Twain', uri='https://viaf.org/viaf/50566653',
            rdf_type='http://schema.org/Person')

    def test_str(self):
        subject = self.get_test_subject()
        assert str(subject) == '%s (%s)' % (subject.name, subject.uri)

    def test_repr(self):
        subject = self.get_test_subject()
        assert repr(subject) == '<Subject %s (%s)>' % (subject.uri, subject.name)

    @patch('mep.books.models.requests')
    def test_create_from_uri(self, mock_requests):
        # patch in status codes
        mock_requests.codes = requests.codes
        mock_response = mock_requests.get.return_value
        # simulate success and return local fixture rdf data
        mock_response.status_code = requests.codes.ok
        with open(os.path.join(FIXTURE_DIR, 'viaf_97006051.rdf')) as rdf_file:
            mock_response.content.decode.return_value = rdf_file.read()
            # needs to be not text/html
            mock_response.headers = {'content-type': 'application/rdf+xml'}

        viaf_uri = 'http://viaf.org/viaf/97006051'
        new_subject = Subject.create_from_uri(viaf_uri)
        # should create subject with fields populated
        assert isinstance(new_subject, Subject)
        assert new_subject.uri == viaf_uri
        assert new_subject.rdf_type == 'http://schema.org/Person'
        assert new_subject.name == 'Ernest Hemingway'
        # should be saved
        assert new_subject.pk
        # viaf URI should be called with accept haeder for content-negotiation
        mock_requests.get.assert_called_with(
            viaf_uri, headers={'accept': 'application/rdf+xml'})

        # simulate no label
        mock_response.content.decode.return_value = '''<rdf:RDF
        xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" />'''
        assert not Subject.create_from_uri(viaf_uri)

        # simulate success but html
        mock_response.headers = {'content-type': 'text/html; charset=UTF-8'}
        # doesn't error but doesn't return anything
        assert not Subject.create_from_uri(viaf_uri)

        # test LoC url with json-ld response
        with open(os.path.join(FIXTURE_DIR, 'loc_sh2008113651.jsonld')) as jsonld_file:
            mock_response.content.decode.return_value = jsonld_file.read()
            mock_response.headers = {'content-type': 'application/ld+json'}
            loc_uri = 'http://id.loc.gov/authorities/subjects/sh2008113651'
            new_subject = Subject.create_from_uri(loc_uri)
            assert isinstance(new_subject, Subject)
            assert new_subject.uri == loc_uri
            # order is not guaranteed so we get *one* of these
            # (but I don't think we care)
            assert new_subject.rdf_type in [
                'http://www.w3.org/2004/02/skos/core#Concept',
                'http://www.loc.gov/mads/rdf/v1#ComplexSubject'
            ]
            assert new_subject.name == 'Women--Economic conditions'

            # explicitly requests jsonld version for LoC url
            mock_requests.get.assert_called_with('%s.jsonld' % loc_uri,
                                                 headers={})

        # simulate not found
        mock_response.status_code = requests.codes.not_found
        fast_uri = 'http://id.worldcat.org/fast/1259831/'
        new_subject = Subject.create_from_uri(fast_uri)
        assert not new_subject
        # fast URI requires different http request
        mock_requests.get.assert_called_with(
            '%s.rdf.xml' % fast_uri.rstrip('/'), headers={})
