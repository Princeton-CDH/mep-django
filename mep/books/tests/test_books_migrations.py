
from django.apps import apps
from django.conf import settings
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
import pytest

from mep.accounts.models import Account, Event
from mep.accounts.tests.test_accounts_migrations import TestMigrations
import mep.books.migration_group_work_utils as merge_utils
from mep.books.models import Creator, CreatorType, Work
from mep.people.models import Person


def test_similar_titles():

    # single title
    assert merge_utils.similar_titles(['Helene'])

    # exact same
    assert merge_utils.similar_titles(['Helene', 'Helene'])

    # variance in definite article and similar
    assert merge_utils.similar_titles(['New Yorker', 'The New Yorker'])
    assert merge_utils.similar_titles([
        'The New Poetry: Anthology of Twentieth Century Verse in English',
        'The New Poetry: An Anthology of Twentieth-Century Verse in English'
    ])

    # variance in upper/lower case
    assert merge_utils.similar_titles(['New Yorker', 'a new yorker'])

    # slugify flattens accents
    assert merge_utils.similar_titles(['Françoise', 'Francoise'])

    # variation in initials
    assert merge_utils.similar_titles(['Short Stories of H.G. Wells',
                                       'Short Stories of H. G. Wells'])

    assert merge_utils.similar_titles(['Collected Poems of H.D.',
                                       'Collected Poems of H. D.'])

    # em dash and regular dash
    assert merge_utils.similar_titles(['Collected Poems, 1909–1935',
                                       'Collected Poems, 1909-1935'])

    # not close enough
    assert not merge_utils.similar_titles(['Collected Poems, 1909–1935',
                                           'Collected Poems'])


@pytest.mark.django_db
def test_ok_to_merge():

    # create two works with different titles and no creators
    work1 = Work.objects.create(title='New York')
    work2 = Work.objects.create(title='The New Yorker')
    assert not merge_utils.ok_to_merge(Work.objects.all())

    # create two works with similar titles and no creators
    work1.title = 'New Yorker'
    work1.save()
    assert merge_utils.ok_to_merge(Work.objects.all())

    # add an author to one
    author = CreatorType.objects.get(name='Author')
    person = Person.objects.create(name='John Foo', slug='foo')
    Creator.objects.create(person=person, creator_type=author, work=work1)
    assert not merge_utils.ok_to_merge(Work.objects.all())

    # match authors on works
    Creator.objects.create(person=person, creator_type=author, work=work2)
    assert merge_utils.ok_to_merge(Work.objects.all())


@pytest.mark.django_db
def test_create_logentry():
    myobj = CreatorType.objects.first()
    msg = 'test change log'
    merge_utils.create_logentry(myobj, repr(myobj), msg, apps)
    script_user = User.objects.get(username=settings.SCRIPT_USERNAME)
    obj_content_type = ContentType.objects.get_for_model(CreatorType)

    # get the most recently created log entry and inspect
    last_log = LogEntry.objects.last()
    assert last_log.user_id == script_user.id
    assert last_log.content_type_id == obj_content_type.pk
    assert int(last_log.object_id) == myobj.pk
    assert last_log.object_repr == repr(myobj)
    assert last_log.change_message == msg
    assert last_log.action_flag == CHANGE


class TestMergeWorks(TestCase):
    fixtures = ['sample_works']

    def test_merge(self):
        # test basic merge functionality

        # get a work from the fixture and make a copy to merge
        work = Work.objects.filter(uri__isnull=False).first()
        work2 = Work.objects.create(title=work.title, uri=work.uri,
                                    ebook_url='http://example.com/mybook.pub')

        merged_work = merge_utils.merge_works(
            Work.objects.filter(uri=work.uri), apps)

        # should copy attributes
        assert merged_work.ebook_url == work2.ebook_url
        # should document the merge in notes
        assert 'Merged on' in merged_work.notes
        assert 'with %d' % work2.pk in merged_work.notes
        # should not flag for title variation
        assert 'TITLEVAR' not in Work.objects.get(pk=work.pk).notes
        # creates a log entry to document the change
        assert LogEntry.objects.filter(object_id=work.pk,
                                       action_flag=CHANGE).count() == 1

        # second work should be gone
        assert not Work.objects.filter(pk=work2.pk).exists()

    def test_title_variation(self):
        # title variation should be flagged in notes
        work = Work.objects.filter(uri__isnull=False).first()
        Work.objects.create(title='Alternate title', uri=work.uri)

        merged_work = merge_utils.merge_works(
            Work.objects.filter(uri=work.uri), apps)
        assert 'TITLEVAR' in merged_work.notes

    def test_year_variation(self):
        # get a work with a uri & a year
        work = Work.objects.get(mep_id='exite')
        work2 = Work.objects.create(title=work.title, uri=work.uri,
                                    year=work.year - 3)

        merged_work = merge_utils.merge_works(
            Work.objects.filter(uri=work.uri), apps)
        # should use the earliest year among all works
        assert merged_work.year == work2.year

    def test_merge_creators(self):
        # has uri + one author
        work = Work.objects.get(mep_id='exite')
        work2 = Work.objects.create(title=work.title, uri=work.uri)
        author = CreatorType.objects.get(name='Author')
        auth2 = Person.objects.create(name='Jean Foo', slug='foo')
        # put on both works to test cleanup
        creator_w1 = Creator.objects.create(
            person=auth2, creator_type=author, work=work)
        creator_w2 = Creator.objects.create(
            person=auth2, creator_type=author, work=work2)
        translator = CreatorType.objects.get(name='Translator')
        translat2 = Person.objects.create(name='Jean LeNoir', slug='lenoir')
        Creator.objects.create(person=translat2, creator_type=translator,
                               work=work2)

        merged_work = merge_utils.merge_works(
            Work.objects.filter(uri=work.uri), apps)
        # original + one from work2
        assert merged_work.authors.count() == 2
        # shouldn't technically be on works, but allowed and test
        assert merged_work.translators.count() == 1
        # redundant creator record removed
        assert not Creator.objects.filter(pk=creator_w2.pk).exists()

    def test_move_events(self):
        work = Work.objects.get(mep_id='exite')
        work2 = Work.objects.create(title=work.title, uri=work.uri)
        # create events to test they are moved properly
        acct = Account.objects.create()
        Event.objects.create(account=acct, work=work)
        Event.objects.create(account=acct, work=work2)
        Event.objects.create(account=acct, work=work2)

        merged_work = merge_utils.merge_works(
            Work.objects.filter(uri=work.uri), apps)

        assert merged_work.event_set.count() == 3


@pytest.mark.last
class GroupWorksbyUri(TestMigrations):

    app = 'books'
    migrate_from = '0015_split_work_edition'
    migrate_to = '0016_group_works_by_uri'

    def setUpBeforeMigration(self, apps):
        Work = apps.get_model('books', 'Work')
        User = apps.get_model('auth', 'User')

        # script user needed for log entry logic
        User.objects.create(username=settings.SCRIPT_USERNAME)

        # create works to test merge logic

        # matching uri, but similar title - merge
        self.ny1 = Work.objects.create(
            title='New Yorker',
            uri='http://worldcat.org/entity/work/id/1151032126')
        self.ny2 = Work.objects.create(
            title='The New Yorker',
            uri='http://worldcat.org/entity/work/id/1151032126')

        # same uri but different titles, not ok to merge
        self.letters1 = Work.objects.create(
            title='Life & Letters',
            uri='http://example.com/work/ll11235')
        self.letters2 = Work.objects.create(
            title='Life & Letters of Somebody Else',
            uri='http://example.com/work/ll11235')

        # no uri - ignored
        self.no_uri = Work.objects.create(title='Unidentified')

        # single uri - ignored
        self.single_uri = Work.objects.create(
            title='Unusual', uri='http://example.com/work/unusual')

        self.work_count = Work.objects.count()

    def test_merge(self):

        # total after merge should be one less
        assert Work.objects.count() == self.work_count - 1
        # ny2 should be gone after the merge
        assert not Work.objects.filter(pk=self.ny2.pk).exists()
