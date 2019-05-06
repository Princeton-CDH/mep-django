import codecs
from collections import defaultdict
import datetime
from io import StringIO
import os
from tempfile import NamedTemporaryFile
from unittest.mock import patch, Mock

from django.contrib.admin.models import LogEntry, CHANGE
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
import pymarc

from mep.books.management.commands import reconcile_oclc
from mep.books.models import Item, CreatorType, Creator
from mep.people.models import Person
from mep.books.tests.test_oclc import get_srwresponse_xml_fixture


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
        assert '0 items to reconcile' in output
        # no file output
        assert not os.stat(csvtempfile.name).st_size
        # no progbar
        mockprogressbar.ProgressBar.assert_not_called()

        # create items that should be ignored
        # generic, problem, title*, zero, existing uri
        Item.objects.create(notes="GENERIC can't identify")
        Item.objects.create(notes="PROBLEM some problematic issue here")
        Item.objects.create(notes="OBSCURE")
        Item.objects.create(title="Plays*")
        Item.objects.create(notes="ZERO no borrows")
        Item.objects.create(
            title='Mark Twain\'s notebook',
            uri='http://experiment.worldcat.org/entity/work/data/477260')
        stdout = StringIO()
        call_command('reconcile_oclc', 'report', '-o', csvtempfile.name,
                     stdout=stdout)
        output = stdout.getvalue()
        assert '0 items to reconcile' in output
        # no file output
        assert not os.stat(csvtempfile.name).st_size
        # no progbar
        mockprogressbar.ProgressBar.assert_not_called()

        # create items that should be processed
        item1 = Item.objects.create(title="Patriotic Adventurer", year=1936)
        # with one author to sanity-check included in output
        ctype = CreatorType.objects.get(name='Author')
        person = Person.objects.create(sort_name='Ireland, Denis')
        Creator.objects.create(creator_type=ctype, person=person, item=item1)
        item2 = Item.objects.create(title="Crowded House", notes="Variant title")
        stdout = StringIO()
        # return no matches for one, some for the second
        mock_oclc_info.side_effect = {'# matches': 0}, {"# matches": 5}
        call_command('reconcile_oclc', 'report', '-o', csvtempfile.name,
                     stdout=stdout)
        output = stdout.getvalue()
        assert '2 items to reconcile' in output
        # search should be called once for each non-skipped item
        assert mock_oclc_info.call_count == 2
        # summary output
        assert 'Processed 2 items, found matches for 1' in output

        # test running update from command line
        with patch('mep.books.management.commands.reconcile_oclc.Command.oclc_search_record') \
          as mock_oclc_search:

            stdout = StringIO()
            mock_oclc_search.return_value = None
            call_command('reconcile_oclc', 'update', stdout=stdout)
            output = stdout.getvalue()
            print(output)
            assert mock_oclc_search.call_count == 2
            assert '2 items to reconcile' in output
            # summary output for update mode
            assert 'Processed 2 items, updated 0' in output

        # create enough items to trigger progressbar
        for title in range(5):
            Item.objects.create(title=title)
        mock_oclc_info.side_effect = None
        call_command('reconcile_oclc', 'report', '-o', csvtempfile.name,
                     stdout=stdout)
        # progbar initialized
        mockprogressbar.ProgressBar.assert_called_with(
            redirect_stdout=True, max_value=7) # 5 + 2
        # progbar updated
        assert mockprogressbar.ProgressBar.return_value.update.call_count == 7
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

            # create items to be processed
            item1 = Item.objects.create(title="Patriotic Adventurer", year=1936)
            # with one author to sanity-check included in output
            ctype = CreatorType.objects.get(name='Author')
            person = Person.objects.create(sort_name='Ireland, Denis')
            Creator.objects.create(creator_type=ctype, person=person, item=item1)
            item2 = Item.objects.create(title="Crowded House", notes="Variant title")

            csvtempfile = NamedTemporaryFile(suffix='csv')
            self.cmd.report([item1, item2], csvtempfile.name)

       # check csvfile contents
        csvtempfile.seek(0)
        csv_content = csvtempfile.read().decode()
        # csv output should have byte-order marck
        assert csv_content.startswith(codecs.BOM_UTF8.decode())
        # csv output should have header row
        assert ','.join(self.cmd.csv_fieldnames) in csv_content
        # csv output should include summary book details from db
        assert item1.title in csv_content
        assert str(item1.year) in csv_content
        assert str(person) in csv_content
        assert item2.title in csv_content
        assert item2.notes in csv_content
        # oclc results should all be present (str to accommodate int match count)
        for value in mock_result_info.values():
            assert str(value) in csv_content

        assert self.cmd.stats['count'] == 2
        assert self.cmd.stats['found'] == 1

    def test_update_items(self):
        item1 = Item.objects.create(title="Time + Tide")
        with patch.object(self.cmd, 'oclc_search_record') as mock_oclc_search:
            # use a mock for the world cat entity
            worldcat_entity = Mock(
                work_uri='http://worldcat.org/entity/work/id/3372107206',
                item_uri='http://www.worldcat.org/oclc/3484871',
                genre='Periodicals',
                item_type='http://schema.org/Periodical',
                subjects=[]
            )
            mock_oclc_search.return_value = worldcat_entity
            self.cmd.update_items([item1])

            # confirm that item was saved with changes
            item = Item.objects.get(pk=item1.pk)
            assert item.genre
            assert item.uri

            assert self.cmd.stats['count'] == 1
            assert self.cmd.stats['updated'] == 1

            # should create a log entry
            log_entry = LogEntry.objects.get(object_id=item.pk)
            assert log_entry.action_flag == CHANGE
            assert log_entry.change_message == \
                'Updated from OCLC %s' % worldcat_entity.item_uri

            # simulate failure on search
            mock_oclc_search.return_value = None
            # reset stats
            self.cmd.stats = defaultdict(int)
            self.cmd.update_items([item1])
            assert self.cmd.stats['count'] == 1
            assert self.cmd.stats['updated'] == 0

    def test_oclc_search(self):
        mock_sru_search = Mock()
        self.cmd.sru_search = mock_sru_search
        # use SRW response fixture for search response
        srwresponse = get_srwresponse_xml_fixture()
        mock_sru_search.search.return_value = srwresponse

        # search item with title, author, year
        item = Item.objects.create(title="Patriotic Adventurer", year=1936)
        # with one author to sanity-check included in output
        ctype = CreatorType.objects.get(name='Author')
        person = Person.objects.create(sort_name='Ireland, Denis')
        creator = Creator.objects.create(creator_type=ctype, person=person, item=item)

        result = self.cmd.oclc_search(item)
        assert result == srwresponse
        # should search on title, author, year, material type book
        mock_sru_search.search.assert_called_with(
            title__exact=item.title, author__all=str(person),
            year=item.year, material_type__exact='book')

        # search does not include missing fields
        # - delete all but title, no events for first known interaction
        creator.delete()
        item.year = None
        self.cmd.oclc_search(item)
        # should search on title only
        mock_sru_search.search.assert_called_with(
            title__exact=item.title, material_type__exact='book')

        # test filtering by material type  periodical
        item.notes = 'PERIODICAL'
        oclc_info = self.cmd.oclc_search(item)
        mock_sru_search.search.assert_called_with(
            title__exact=item.title, material_type__exact='periodical')

        item.notes = ''
        # simulate no year but first known year from events
        with patch.object(Item, 'first_known_interaction', new=datetime.date(1940, 1, 1)):
            oclc_info = self.cmd.oclc_search(item)
            # should search on title and year range
            mock_sru_search.search.assert_called_with(
                title__exact=item.title, year="-1940",
                material_type__exact='book')

    def test_oclc_info(self):
        srwresponse = get_srwresponse_xml_fixture()
        # search item with title, author, year
        mock_item = Mock()
        mock_sru_search = Mock()
        self.cmd.sru_search = mock_sru_search

        with patch.object(self.cmd, 'oclc_search') as mock_oclc_search:
            mock_oclc_search.return_value = srwresponse
            oclc_info = self.cmd.oclc_info(mock_item)
            mock_oclc_search.assert_called_with(mock_item)

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
        assert oclc_info['OCLC URI'] == mock_wc_rdf.item_uri
        assert oclc_info['Work URI'] == mock_wc_rdf.work_uri

        # simulate no results found
        with patch.object(self.cmd, 'oclc_search') as mock_oclc_search:
            mock_oclc_search.return_value = srwresponse
            srwresponse.num_records = 0
            oclc_info = self.cmd.oclc_info(mock_item)
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
        item = Item(title='tester')

        with patch.object(self.cmd, 'oclc_search') as mock_oclc_search:
            self.cmd.sru_search = Mock()
            mock_oclc_search.return_value = srwresponse
            srwresponse.num_records = 0
            # should return nothing if zero records
            assert not self.cmd.oclc_search_record(item)
            srwresponse.num_records = 1

            result = self.cmd.oclc_search_record(item)
            assert self.cmd.sru_search.get_worldcat_rdf.call_count == 1
            assert result == self.cmd.sru_search.get_worldcat_rdf.return_value
            call_args = self.cmd.sru_search.get_worldcat_rdf.call_args[0]
            # can't compare pymarc records exactly so check type
            assert isinstance(call_args[0], pymarc.record.Record)
