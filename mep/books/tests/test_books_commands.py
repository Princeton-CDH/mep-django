import codecs
from collections import defaultdict
import datetime
from io import StringIO
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import patch, Mock

from django.contrib.admin.models import LogEntry, CHANGE
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
import pymarc
import pytest

from mep.books.management.commands import reconcile_oclc
from mep.books.models import Creator, CreatorType, Work
from mep.books.tests.test_oclc import get_srwresponse_xml_fixture
from mep.people.models import Person
from mep.common.utils import absolutize_url


class TestReconcileOCLC(TestCase):

    def setUp(self):
        self.cmd = reconcile_oclc.Command()
        self.cmd.stdout = StringIO()

    @override_settings(OCLC_WSKEY='secretkey')
    @patch('mep.books.management.commands.reconcile_oclc.progressbar')
    @patch.object(reconcile_oclc.Command, 'oclc_info')
    def test_command_line(self, mock_oclc_info, mockprogressbar):
        # test calling via command line with args
        csvtempfile = NamedTemporaryFile(suffix='csv')
        stdout = StringIO()
        call_command('reconcile_oclc', 'report', '-o', csvtempfile.name,
                     stdout=stdout)
        output = stdout.getvalue()
        assert '0 works to reconcile' in output
        # no file output
        assert not os.stat(csvtempfile.name).st_size
        # no progbar
        mockprogressbar.ProgressBar.assert_not_called()

        # create works that should be ignored
        # generic, problem, title*, zero, existing uri, previous no match
        Work.objects.create(notes="GENERIC can't identify", slug='generic')
        Work.objects.create(notes="PROBLEM some problematic issue here",
                            slug='problem')
        Work.objects.create(notes="OBSCURE", slug="obscure")
        Work.objects.create(title="Plays*", slug="plays")
        Work.objects.create(notes="ZERO no borrows", slug="zero")
        Work.objects.create(notes="OCLCNoMatch", slug="nomatch")
        Work.objects.create(
            title='Mark Twain\'s notebook',
            uri='http://experiment.worldcat.org/entity/work/data/477260',
            slug="mark-twains-notebook")
        stdout = StringIO()
        call_command('reconcile_oclc', 'report', '-o', csvtempfile.name,
                     stdout=stdout)
        output = stdout.getvalue()
        assert '0 works to reconcile' in output
        # no file output
        assert not os.stat(csvtempfile.name).st_size
        # no progbar
        mockprogressbar.ProgressBar.assert_not_called()

        # create works that should be processed
        work1 = Work.objects.create(title="Patriotic Adventurer", year=1936,
                                    slug="patriotic")
        # with one author to sanity-check included in output
        ctype = CreatorType.objects.get(name='Author')
        person = Person.objects.create(sort_name='Ireland, Denis')
        Creator.objects.create(creator_type=ctype, person=person, work=work1)
        work2 = Work.objects.create(title="Crowded House",
                                    notes="Variant title", slug="crowded")
        stdout = StringIO()
        # return no matches for one, some for the second
        mock_oclc_info.side_effect = {'# matches': 0}, {"# matches": 5}
        call_command('reconcile_oclc', 'report', '-o', csvtempfile.name,
                     stdout=stdout)
        output = stdout.getvalue()
        assert '2 works to reconcile' in output
        # search should be called once for each non-skipped work
        assert mock_oclc_info.call_count == 2
        # summary output
        assert 'Processed 2 works, found matches for 1' in output

        # test running update from command line
        with patch('mep.books.management.commands.reconcile_oclc.Command.oclc_search_record') \
          as mock_oclc_search:

            stdout = StringIO()
            mock_oclc_search.return_value = None
            call_command('reconcile_oclc', 'update', stdout=stdout)
            output = stdout.getvalue()
            assert mock_oclc_search.call_count == 2
            assert '2 works to reconcile' in output
            # summary output for update mode
            assert 'Processed 2 works, updated 0' in output

        # create enough works to trigger progressbar
        for title in range(6):
            Work.objects.create(title=str(title), slug='%s' % title)
        mock_oclc_info.side_effect = None
        call_command('reconcile_oclc', 'report', '-o', csvtempfile.name,
                     stdout=stdout)
        # progbar initialized
        mockprogressbar.ProgressBar.assert_called_with(
            redirect_stdout=True, max_value=6)
        # progbar updated
        assert mockprogressbar.ProgressBar.return_value.update.call_count == 6
        mockprogressbar.ProgressBar.return_value.finish.assert_called_with()

        # no progress option respected
        mockprogressbar.reset_mock()
        call_command('reconcile_oclc', 'report', '-o', csvtempfile.name,
                     '--no-progress', stdout=stdout)
        mockprogressbar.ProgressBar.assert_not_called()

    def test_report(self):
        with patch.object(self.cmd, 'oclc_info') as mock_oclc_info:
            mock_result_info = {
                "# matches": 5,
                'OCLC Title': 'Patriot Adventurer',
                'OCLC Author': 'Denis Ireland',
                'OCLC Date': 1936,
                'OCLC URI': 'http://worldcat.org/entity/work/id/49679151',
                'Work URI': 'http://www.worldcat.org/oclc/65986486'
            }
            mock_oclc_info.side_effect = mock_result_info, {'# matches': 0}

            # create works to be processed
            work1 = Work.objects.create(title="Patriotic Adventurer",
                                        year=1936, slug="patriotic-adv")
            # with one author to sanity-check included in output
            ctype = CreatorType.objects.get(name='Author')
            person = Person.objects.create(sort_name='Ireland, Denis', slug='d')
            Creator.objects.create(creator_type=ctype, person=person, work=work1)
            work2 = Work.objects.create(title="Crowded House",
                                        notes="Variant title", slug="crowd")

            csvtempfile = NamedTemporaryFile(suffix='csv')
            self.cmd.report([work1, work2], csvtempfile.name)

        # check csvfile contents
        csvtempfile.seek(0)
        csv_content = csvtempfile.read().decode()
        # csv output should have byte-order marck
        assert csv_content.startswith(codecs.BOM_UTF8.decode())
        # csv output should have header row
        assert ','.join(self.cmd.csv_fieldnames) in csv_content
        # csv output should include summary book details from db
        assert work1.title in csv_content
        assert str(work1.year) in csv_content
        assert str(person) in csv_content
        assert work2.title in csv_content
        assert work2.notes in csv_content
        # oclc results should all be present (str to accommodate int match count)
        for value in mock_result_info.values():
            assert str(value) in csv_content

        assert self.cmd.stats['count'] == 2
        assert self.cmd.stats['found'] == 1

    def test_update_works(self):
        work1 = Work.objects.create(title="Time + Tide", notes='some notes',
                                    slug="time-tide")
        with patch.object(self.cmd, 'oclc_search_record') as mock_oclc_search:
            # use a mock for the world cat entity
            worldcat_entity = Mock(
                work_uri='http://worldcat.org/entity/work/id/3372107206',
                item_uri='http://www.worldcat.org/oclc/3484871',
                genres=['Periodicals'],
                item_type='http://schema.org/Periodical',
                subjects=[]
            )
            mock_oclc_search.return_value = worldcat_entity
            self.cmd.update_works([work1])

            # confirm that work was saved with changes
            work = Work.objects.get(pk=work1.pk)
            assert work.genres.first().name == 'Periodicals'
            assert work.uri

            assert self.cmd.stats['count'] == 1
            assert self.cmd.stats['updated'] == 1
            assert self.cmd.stats['no_match'] == 0

            # should create a log entry
            log_entry = LogEntry.objects.get(object_id=work.pk)
            assert log_entry.action_flag == CHANGE
            assert log_entry.change_message == \
                'Updated from OCLC %s' % worldcat_entity.work_uri
            # delete for simplicity in subsequent tests
            log_entry.delete()

            # simulate failure loading worldcat rdf
            mock_oclc_search.side_effect = ConnectionError
            self.cmd.stderr = StringIO()
            self.cmd.stats = defaultdict(int)
            # shouldn't blow up
            self.cmd.update_works([work1])
            output = self.cmd.stderr.getvalue()
            assert 'Error:' in output
            # shouldn't update anything
            assert self.cmd.stats['count'] == 1
            assert self.cmd.stats['updated'] == 0

            # simulate no results from search
            mock_oclc_search.return_value = None
            mock_oclc_search.side_effect = None
            # reset stats
            self.cmd.stats = defaultdict(int)
            self.cmd.update_works([work1])
            assert self.cmd.stats['count'] == 1
            assert self.cmd.stats['updated'] == 0
            assert self.cmd.stats['no_match'] == 1
            # should add to notes
            updated_work = Work.objects.get(pk=work.pk)
            # should include no match indicator
            assert self.cmd.oclc_no_match in updated_work.notes
            # should still have previous note content
            assert work.notes in updated_work.notes
            # should create a log entry indicating no match found
            log_entry = LogEntry.objects.get(object_id=work.pk)
            assert log_entry.action_flag == CHANGE
            assert log_entry.change_message == \
                'No OCLC match found'

    def test_oclc_search(self):
        mock_sru_search = Mock()
        self.cmd.sru_search = mock_sru_search
        # use SRW response fixture for search response
        srwresponse = get_srwresponse_xml_fixture()
        mock_sru_search.search.return_value = srwresponse

        # all searches will include these filters
        default_filters = {
            'language_code__exact': 'eng',
            'material_type__notexact': 'Internet Resource'
        }

        # search work with title, author, year
        work = Work.objects.create(title="Patriotic Adventurer", year=1936,
                                   slug="patriotic-adventurer")
        # with one author to sanity-check included in output
        ctype = CreatorType.objects.get(name='Author')
        person = Person.objects.create(sort_name='Ireland, Denis', slug='di')
        creator = Creator.objects.create(creator_type=ctype, person=person,
                                         work=work)

        result = self.cmd.oclc_search(work)
        assert result == srwresponse
        # should search on title, author, year, material type book;
        # filter to english language, non ebook
        mock_sru_search.search.assert_called_with(
            title__exact=work.title, author__all=str(person),
            year=work.year, material_type__exact='book',
            **default_filters
        )

        # search does not include missing fields
        # - delete all but title, no events for first known interaction
        creator.delete()
        work.year = None
        self.cmd.oclc_search(work)
        # should search on title only
        mock_sru_search.search.assert_called_with(
            title__exact=work.title, material_type__exact='book',
            **default_filters)

        # test filtering by material type  periodical
        work.notes = 'PERIODICAL'
        oclc_info = self.cmd.oclc_search(work)
        mock_sru_search.search.assert_called_with(
            title__exact=work.title, material_type__exact='periodical',
            **default_filters)

        work.notes = ''
        # simulate no year but first known year from events
        with patch.object(Work, 'first_known_interaction', new=datetime.date(1940, 1, 1)):
            oclc_info = self.cmd.oclc_search(work)
            # should search on title and year range
            mock_sru_search.search.assert_called_with(
                title__exact=work.title, year="-1940",
                material_type__exact='book',
                **default_filters)

    def test_oclc_info(self):
        srwresponse = get_srwresponse_xml_fixture()
        # search work with title, author, year
        mock_work = Mock(notes='')
        mock_sru_search = Mock()
        self.cmd.sru_search = mock_sru_search

        with patch.object(self.cmd, 'oclc_search') as mock_oclc_search:
            mock_oclc_search.return_value = srwresponse
            oclc_info = self.cmd.oclc_info(mock_work)
            mock_oclc_search.assert_called_with(mock_work)

        # uses first marc record in the response
        marc_record = srwresponse.marc_records[0]
        # can't use assert called with because marc record objects
        # are different, since they are generated dynamically by pymarc
        assert mock_sru_search.get_worldcat_rdf.call_count == 1
        args = mock_sru_search.get_worldcat_rdf.call_args[0]
        assert isinstance(args[0], pymarc.record.Record)

        mock_wc_rdf = mock_sru_search.get_worldcat_rdf.return_value

        # inspect returned details
        assert oclc_info['# matches'] == srwresponse.num_records
        assert oclc_info['OCLC Title'] == marc_record.title()
        assert oclc_info['OCLC Author'] == marc_record.author()
        assert oclc_info['OCLC Date'] == marc_record.pubyear()
        assert oclc_info['OCLC URI'] == mock_wc_rdf.work_uri
        assert oclc_info['Work URI'] == mock_wc_rdf.work_uri

        # simulate error loading worldcat rdf
        mock_sru_search.get_worldcat_rdf.side_effect = ConnectionError
        self.cmd.stderr = StringIO()
        with patch.object(self.cmd, 'oclc_search') as mock_oclc_search:
            mock_oclc_search.return_value = srwresponse
            oclc_info = self.cmd.oclc_info(mock_work)
        # only includes count
        assert len(oclc_info.keys()) == 1
        assert oclc_info['# matches'] == srwresponse.num_records
        output = self.cmd.stderr.getvalue()
        assert 'Error:' in output

        # simulate no results found
        with patch.object(self.cmd, 'oclc_search') as mock_oclc_search:
            mock_oclc_search.return_value = srwresponse
            srwresponse.num_records = 0
            oclc_info = self.cmd.oclc_info(mock_work)
        # should report 0 matches and nothing else
        assert oclc_info['# matches'] == 0
        assert len(oclc_info) == 1

    def test_tick(self):
        # tick with no progressbar
        self.cmd.tick()
        assert self.cmd.stats['count'] == 1
        assert not self.cmd.progbar

        # with progress bar
        self.cmd.progbar = Mock()
        self.cmd.tick()
        assert self.cmd.stats['count'] == 2
        self.cmd.progbar.update.assert_called_with(2)

    def test_oclc_search_record(self):
        srwresponse = get_srwresponse_xml_fixture()
        work = Work(title='tester')

        with patch.object(self.cmd, 'oclc_search') as mock_oclc_search:
            self.cmd.sru_search = Mock()
            mock_oclc_search.return_value = srwresponse
            srwresponse.num_records = 0
            # should return nothing if zero records
            assert not self.cmd.oclc_search_record(work)
            srwresponse.num_records = 1

            result = self.cmd.oclc_search_record(work)
            assert self.cmd.sru_search.get_worldcat_rdf.call_count == 1
            assert result == self.cmd.sru_search.get_worldcat_rdf.return_value
            call_args = self.cmd.sru_search.get_worldcat_rdf.call_args[0]
            # can't compare pymarc records exactly so check type
            assert isinstance(call_args[0], pymarc.record.Record)


@pytest.mark.django_db
class TestExportBooks(TestCase):
    fixtures = ['sample_works']

    def setUp(self):
        # importing here because it queries the database at definition time
        from mep.books.management.commands import export_books

        self.cmd = export_books.Command()
        self.cmd.stdout = StringIO()

    def test_filename(self):
        assert self.cmd.get_base_filename() == 'books'

    def test_get_object_data(self):
        exit_e = Work.objects.count_events().get(slug='exit-eliza')
        data = self.cmd.get_object_data(exit_e)
        assert data['uri'] == absolutize_url(exit_e.get_absolute_url())
        assert data['title'] == exit_e.title
        assert data['year'] == exit_e.year
        assert data['format'] == exit_e.work_format.name
        assert data['identified']  # not marked uncertain
        assert 'work_uri' not in data
        assert 'author' in data
        # missing data should not be in the dict
        for field in ['edition uri', 'ebook url', 'volumes/issues']:
            assert field not in data
        assert data['event_count'] == exit_e.event__count
        assert data['borrow_count'] == exit_e.event__borrow__count
        assert data['purchase_count'] == exit_e.event__purchase__count
        assert data['updated'] == exit_e.updated_at.isoformat()
        # fixture has no events for exit eliza, so no years are set
        assert data['circulation_years'] == []

        # infer format = book if format is unset and item not uncertain
        exit_e.work_format = None
        assert self.cmd.get_object_data(exit_e)['format'] == 'Book'
        exit_e.notes = 'UNCERTAINTYICON'
        assert 'format' not in self.cmd.get_object_data(exit_e)

        # record with different data
        dial = Work.objects.count_events().get(slug='dial')
        data = self.cmd.get_object_data(dial)
        assert 'year' not in data
        assert 'edition_uri' not in data
        assert data['ebook_url'] == dial.ebook_url
        assert 'volumes_issues' in data
        assert data['format'] == dial.work_format.name
        for vol in dial.edition_set.all():
            assert vol.display_text() in data['volumes_issues']
        assert data['circulation_years'] == [1936]

    def test_creator_info(self):
        exit_e = Work.objects.count_events().get(slug='exit-eliza')
        data = self.cmd.creator_info(exit_e)
        assert data['author'] == [exit_e.authors[0].sort_name]
        for creator in ['editor', 'translator', 'illustrator']:
            assert creator not in data

    def test_command_line(self):
        # test calling via command line with args
        tempdir = TemporaryDirectory()
        stdout = StringIO()
        call_command('export_books', '-d', tempdir.name, stdout=stdout)
        output = stdout.getvalue()
        assert 'Exporting JSON' in output
        assert 'Exporting CSV' in output
        assert os.path.exists(os.path.join(tempdir.name, 'books.json'))
        assert os.path.exists(os.path.join(tempdir.name, 'books.csv'))

        with patch('mep.books.management.commands.export_books' +
                   '.Command.get_object_data') as mock_get_obj_data:
            mock_get_obj_data.return_value = {'title': 'test'}
            call_command('export_books', '-d', tempdir.name, '-m', 2,
                         stdout=stdout)
            # 2 mock objects * 2 (once each for CSV, JSON)
            assert mock_get_obj_data.call_count == 4
