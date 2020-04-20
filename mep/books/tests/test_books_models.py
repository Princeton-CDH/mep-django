import datetime
import os
from unittest.mock import Mock, patch

from django.test import TestCase
import requests

from mep.accounts.models import Account, Borrow, Event, Purchase
from mep.books.models import Creator, CreatorType, Edition, EditionCreator, \
    Format, Genre, Subject, Work
from mep.books.utils import work_slug
from mep.books.tests.test_oclc import FIXTURE_DIR
from mep.people.models import Person


class TestWork(TestCase):

    def test_repr(self):
        work = Work(title='Le foo et le bar', year=1916)
        # unsaved
        assert repr(work) == '<Work pk:?? %s>' % work
        # saved
        work.save()
        assert repr(work) == '<Work pk:%s %s>' % (work.pk, work)

    def test_str(self):

        # Test pattern for title and year
        work = Work(title='Le foo et le bar', year=1916)
        assert str(work) == 'Le foo et le bar (1916)'
        # Test pattern for just title
        work.year = None
        assert str(work) == 'Le foo et le bar'
        # Test pattern for no title or year
        work.title = ''
        assert str(work) == '(No title, year)'

    def test_borrow_count(self):
        # create a test work
        # should have zero borrows
        work = Work(title='Le foo et le bar', year=1916)
        work.save()
        assert work.borrow_count == 0
        # create a test account and borrow the work once
        # should have one borrow
        acct = Account()
        acct.save()
        Borrow(work=work, account=acct).save()
        # borrow a few more times and test the count
        Borrow(work=work, account=acct).save()
        Borrow(work=work, account=acct).save()
        Borrow(work=work, account=acct).save()
        assert work.borrow_count == 4

        # uses db annotation if present
        work.event__borrow__count = 3
        assert work.borrow_count == 3

    def test_event_count(self):
        # create a test work
        # should have zero events
        work = Work(title='Le foo et le bar', year=1916)
        work.save()
        assert work.event_count == 0
        # create a test account and add some events
        acct = Account()
        acct.save()
        Borrow(work=work, account=acct).save()
        # borrow a few more times and test the count
        Purchase(work=work, account=acct).save()
        Event(work=work, account=acct).save()
        assert work.event_count == 3

        # uses db annotation if present
        work.event__count = 12
        assert work.event_count == 12

    def test_purchase_count(self):
        # create a test work
        # should have zero purchases
        work = Work(title='Le foo et le bar', year=1916)
        work.save()
        assert work.purchase_count == 0
        # create a test account and purchase the work once
        # should have one purchase
        acct = Account()
        acct.save()
        Purchase(work=work, account=acct).save()
        # add one borrow
        Borrow(work=work, account=acct).save()
        assert work.purchase_count == 1

        # uses db annotation if present
        work.event__purchase__count = 7
        assert work.purchase_count == 7

    def test_authors_editors_translators(self):
        work = Work.objects.create(title='Poems', year=1916)
        author1 = Person.objects.create(name='Smith', slug='s')
        author2 = Person.objects.create(name='Jones', slug='j')
        editor = Person.objects.create(name='Ed Mund', slug='m')
        translator = Person.objects.create(name='Juan Smythe', slug='sm')
        author_type = CreatorType.objects.get(name='Author')
        editor_type = CreatorType.objects.get(name='Editor')
        translator_type = CreatorType.objects.get(name='Translator')

        # add one each of author, editor, and translator
        Creator.objects.create(
            creator_type=author_type, person=author1, work=work)
        Creator.objects.create(
            creator_type=editor_type, person=editor, work=work)
        Creator.objects.create(
            creator_type=translator_type, person=translator, work=work)

        assert len(work.authors) == 1
        assert work.authors[0] == author1
        assert work.author_list() == str(author1)

        # add second author
        Creator.objects.create(creator_type=author_type, person=author2,
                               work=work)
        assert len(work.authors) == 2
        assert author1 in work.authors
        assert author2 in work.authors
        assert work.author_list() == '%s; %s' % (author1, author2)

        assert len(work.editors) == 1
        assert work.editors[0] == editor

        assert len(work.translators) == 1
        assert work.translators[0] == translator

    def test_format(self):
        work = Work.objects.create(title='Searching')
        assert work.format() == ''

        work.work_format = Format.objects.first()
        assert work.format() == work.work_format.name

    def test_first_known_interaction(self):
        # create a test work with no events
        work = Work.objects.create(title='Searching')
        assert not work.first_known_interaction

        # create a borrow with date
        acct = Account()
        acct.save()
        borrow_date = datetime.date(1940, 3, 2)
        borrow = Borrow(work=work, account=acct)
        borrow.partial_start_date = borrow_date.isoformat()
        borrow.save()
        # first date should be borrow start date
        assert work.first_known_interaction == borrow_date

        # create a borrow with an unknown date
        unknown_borrow = Borrow.objects.create(work=work, account=acct)
        unknown_borrow.partial_start_date = '--01-01'
        unknown_borrow.save()
        # should use previous borrow date, not the unknown (1900)
        assert work.first_known_interaction == borrow_date

    @patch('mep.books.models.Subject.create_from_uri')
    def test_populate_from_worldcat(self, mock_create_from_uri):
        work = Work.objects.create(title='Time and Tide')
        worldcat_entity = Mock(
            work_uri='http://worldcat.org/entity/work/id/3372107206',
            item_uri='http://www.worldcat.org/oclc/3484871',
            genres=['Periodicals'],
            item_type='http://schema.org/Periodical',
            subjects=[]
        )
        work.populate_from_worldcat(worldcat_entity)
        assert work.uri == worldcat_entity.work_uri
        assert work.edition_uri == worldcat_entity.item_uri
        assert work.genres.first().name == worldcat_entity.genres[0]
        assert work.work_format == Format.objects.get(uri=worldcat_entity.item_type)
        # no subjects on the eentity
        assert not work.subjects.all()

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
        work.populate_from_worldcat(worldcat_entity)
        assert work.subjects.count() == 2
        assert mock_create_from_uri.call_count == 2
        mock_create_from_uri.assert_any_call(worldcat_entity.subjects[0])
        mock_create_from_uri.assert_any_call(worldcat_entity.subjects[1])

        # if the subjects already exist, they should not be created
        mock_create_from_uri.reset_mock()
        work.populate_from_worldcat(worldcat_entity)
        mock_create_from_uri.assert_not_called()
        assert work.subjects.count() == 2

        # test replaces previous subjects
        del worldcat_entity.subjects[-1]
        work.populate_from_worldcat(worldcat_entity)
        assert work.subjects.count() == 1

        # simulate error creating subject - returns None
        worldcat_entity.subjects = [
            'http://example.com/about/me',
        ]
        mock_create_from_uri.side_effect = None
        mock_create_from_uri.return_value = None
        # shouldn't error
        work.populate_from_worldcat(worldcat_entity)
        mock_create_from_uri.assert_called_with(worldcat_entity.subjects[0])
        # should set to subjects it could find/create (in this case, none)
        assert not work.subjects.count()

        # unexpected work type / unknown format; should not error
        worldcat_entity.item_type = 'http://schema.org/CreativeWork'
        # clear out existing work format from previous calls
        work.work_format = None
        work.populate_from_worldcat(worldcat_entity)
        assert not work.work_format

    def test_subject_list(self):
        # no subjects
        work = Work.objects.create(title='Topicless')
        assert work.subject_list() == ''

        subj1 = Subject.objects.create(
            uri='http://viaf.org/viaf/97006051', name='Ernest Hemingway',
            rdf_type='http://schema.org/Person')
        subj2 = Subject.objects.create(
            uri='http://id.worldcat.org/fast/1259831/',
            name='Lorton, Virginia', rdf_type='http://schema.org/Place')
        work.subjects.add(subj1)
        work.subjects.add(subj2)
        assert work.subject_list() == '%s; %s' % (subj1.name, subj2.name)

    def test_genre_list(self):
        # no genres
        work = Work.objects.create(title='Genreless')
        assert work.genre_list() == ''

        genre1 = Genre.objects.create(name='Periodicals')
        genre2 = Genre.objects.create(name='Drama')
        work.genres.add(genre1)
        work.genres.add(genre2)
        assert work.genre_list() == '%s; %s' % (genre2.name, genre1.name)

    def test_author_list(self):
        # no authors
        work = Work.objects.create(title='Anonymous')
        assert work.author_list() == ''
        # one author
        author_type = CreatorType.objects.get(name='Author')
        author1 = Person.objects.create(name='Smith', slug='s')
        Creator.objects.create(
            creator_type=author_type, person=author1, work=work)
        assert work.author_list() == 'Smith'
        # multiple authors
        author2 = Person.objects.create(name='Jones', slug='j')
        Creator.objects.create(
            creator_type=author_type, person=author2, work=work)
        assert work.author_list() == 'Smith; Jones'

    def test_sort_author_list(self):
        # no authors
        work = Work.objects.create(title='Anonymous')
        assert work.sort_author_list == ''
        # one author
        author_type = CreatorType.objects.get(name='Author')
        author1 = Person.objects.create(
            name='Bob Smith', sort_name='Smith, Bob', slug='s')
        Creator.objects.create(
            creator_type=author_type, person=author1, work=work)
        assert work.sort_author_list == 'Smith, Bob'
        # multiple authors
        author2 = Person.objects.create(
            name='Bill Jones', sort_name='Jones, Bill', slug='j')
        Creator.objects.create(
            creator_type=author_type, person=author2, work=work)
        assert work.sort_author_list == 'Jones, Bill; Smith, Bob'

    def test_has_uri(self):
        work = Work(title='Topicless')
        assert not work.has_uri()
        work.uri = 'http://www.worldcat.org/oclc/578050'
        assert work.has_uri()

    def test_save(self):
        with patch.object(Work, 'generate_slug') as mock_generate_slug:
            work = Work(title='Topicless', slug='notopic', mep_id='')
            work.save()
            # empty string converted to None
            assert work.mep_id is None
            # generate slug not called
            assert mock_generate_slug.call_count == 0

            # generate slug called if no slug is set
            work.slug = ''
            work.save()
            assert mock_generate_slug.call_count == 1

    def test_generate_slug(self):
        work = Work(title='totally unique title')
        work.generate_slug()
        # uses result of work slug unchanged
        assert work.slug == work_slug(work)
        work.save()

        # three-word title will be a duplicate slug, should use fourth
        work = Work(title='totally unique title 2020')
        work.generate_slug()
        assert work.slug == work_slug(work, max_words=4)

        # numeric differentiation when needed
        Work.objects.create(title='unclear', slug='unclear')
        unclear2 = Work(title='unclear')
        unclear2.generate_slug()
        # should determine -2 based on existing of one unclear slug
        assert unclear2.slug == 'unclear-2'
        unclear2.save()
        # should increment if there are existing numbers
        unclear3 = Work(title='unclear')
        unclear3.generate_slug()
        assert unclear3.slug == 'unclear-3'

    def test_is_uncertain(self):
        # work without notes should not show icon
        work1 = Work(title='My Book')
        assert not work1.is_uncertain
        # work with notes but no UNCERTAINTYICON tag should not show icon
        work2 = Work(title='My Notable Book', notes='my notes')
        assert not work2.is_uncertain
        # work with UNCERTAINTYICON tag should show icon
        work3 = Work(title='Uncertain', notes='foo UNCERTAINTYICON bar')
        assert work3.is_uncertain

    def test_index_data(self):
        work1 = Work.objects.create(
            title='poems', slug='poems', year=1801,
            notes='PROBX', public_notes='some edition')

        data = work1.index_data()
        assert 'item_type' in data
        assert data['pk_i'] == work1.pk
        assert data['title_t'] == work1.title
        assert data['sort_title_isort'] == work1.title
        assert data['slug_s'] == work1.slug
        assert not data['authors_t']
        assert not data['sort_authors_t']
        assert not data['sort_authors_isort']
        assert not data['creators_t']
        assert data['pub_date_i'] == work1.year
        assert data['format_s_lower'] == ''
        assert data['notes_txt_en'] == work1.public_notes
        assert data['admin_notes_txt_en'] == work1.notes
        assert not data['is_uncertain_b']

        # add creators
        ctype = CreatorType.objects.get(name='Author')
        person = Person.objects.create(name='Joyce', slug='joyce',
                                       sort_name='Joyce, J.')
        translator_type = CreatorType.objects.get(name='Translator')
        translator = Person.objects.create(name='Juan Smythe', slug='sm')
        Creator.objects.create(creator_type=ctype, person=person, work=work1)
        Creator.objects.create(creator_type=translator_type, person=translator,
                               work=work1)
        data = work1.index_data()
        assert data['authors_t'] == [a.name for a in work1.authors]
        assert data['sort_authors_t'] == [a.sort_name for a in work1.authors]
        assert data['sort_authors_isort'] == work1.sort_author_list
        assert data['creators_t'] == [c.name for c in work1.creators.all()]


class TestCreator(TestCase):

    def test_str(self):
        ctype = CreatorType.objects.get(name='Author')
        person = Person.objects.create(name='Joyce', slug='joyce')
        work = Work.objects.create(title='Ulysses')
        creator = Creator(creator_type=ctype, person=person, work=work)
        assert str(creator) == ' '.join([str(person), ctype.name, str(work)])


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
                'http://www.loc.gov/mads/rdf/v1#ComplexSubject',
                'http://www.loc.gov/mads/rdf/v1#Authority'
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


class TestEdition(TestCase):

    def test_str(self):
        work = Work.objects.create(title='Le foo et le bar', year=1916,
                                   slug='foo-bar')
        # no edition title or year - uses work details
        edition = Edition(work=work)
        assert str(edition) == '%s (%s)' % (work.title, work.year)

        # edition title takes precedence
        edition.title = 'The foo and the bar'
        assert str(edition) == '%s (%s)' % (edition.title, work.year)

        # edition date takes precedence
        edition.partial_date = '1920'
        assert str(edition) == '%s (%s)' % (edition.title, edition.partial_date)

        # includes volume, number, season when present
        edition.volume = 2
        assert str(edition) == '%s (%s) vol. 2' % (edition.title,
                                                   edition.partial_date)
        edition.number = 3
        assert str(edition) == '%s (%s) vol. 2 no. 3' % \
            (edition.title, edition.partial_date)
        edition.season = 'Winter'
        assert str(edition) == '%s (%s) vol. 2 no. 3 Winter' % \
            (edition.title, edition.partial_date)

        unknown_work = Work.objects.create(slug='unknown')
        # handles missing title
        unknown_edition = Edition(work=unknown_work)
        assert str(unknown_edition) == '?? (??)'

    def test_repr(self):
        work = Work.objects.create(title='Le foo et le bar', year=1916,
                                   slug='foo-bar-1916')
        # unsaved edition has no pk
        edition = Edition(work=work)
        assert repr(edition) == '<Edition pk:?? %s>' % edition

        # saved repr
        edition.save()
        assert repr(edition) == '<Edition pk:%d %s>' % (edition.pk, edition)

    def test_display_html(self):
        work = Work.objects.create(title='transition', slug='transition')
        # volume only
        edition = Edition(work=work, volume=3)
        assert edition.display_html() == 'Vol. 3'
        # volume + number
        edition.number = '19a'
        assert edition.display_html() == 'Vol. 3, no. 19a'
        # volume + number + season
        edition.season = 'Winter'
        assert edition.display_html() == 'Vol. 3, no. 19a, Winter'
        # volume + number + season + year
        edition.date = datetime.date(1931, 1, 1)
        assert edition.display_html() == 'Vol. 3, no. 19a, Winter 1931'
        # number + season + date, no volume
        edition.volume = None
        assert edition.display_html() == 'no. 19a, Winter 1931'
        # with title
        edition.title = 'Subsection'
        assert edition.display_html() == \
            'no. 19a, Winter 1931 <br/><em>Subsection</em>'

        # title and year but no season
        edition.season = ''
        assert edition.display_html() == \
            'no. 19a, 1931 <br/><em>Subsection</em>'

    def test_display_text(self):
        work = Work.objects.create(title='transition', slug='trans')
        # volume only
        edition = Edition(work=work, volume=3,
                          date=datetime.date(1931, 1, 1),
                          title='subtitle')
        assert edition.display_text() == \
            'Vol. 3, 1931 subtitle'


class TestEditionCreator(TestCase):

    def test_str(self):
        ctype = CreatorType.objects.get(name='Editor')
        person = Person.objects.create(name='Joyce', slug='joyce')
        work = Work.objects.create(title='Ulysses')
        edition = Edition.objects.create(work=work)
        creator = EditionCreator(creator_type=ctype, person=person,
                                 edition=edition)
        assert str(creator) == ' '.join([str(person), ctype.name, str(edition)])
