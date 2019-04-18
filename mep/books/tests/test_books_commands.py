import codecs
import datetime
from io import StringIO
import os
from tempfile import NamedTemporaryFile
from unittest.mock import patch, Mock

from django.test import TestCase
from django.core.management import call_command
import pymarc

from mep.books.management.commands import reconcile_oclc
from mep.books.models import Item, CreatorType, Creator
from mep.books.oclc import oclc_uri
from mep.people.models import Person
from mep.books.tests.test_oclc import get_srwresponse_xml_fixture


class TestReconcileOCLC(TestCase):

    def setUp(self):
        self.cmd = reconcile_oclc.Command()
        self.cmd.stdout = StringIO()

    @patch('mep.books.management.commands.reconcile_oclc.progressbar')
    @patch.object(reconcile_oclc.Command, 'oclc_search')
    def test_command_line(self, mock_oclc_search, mockprogressbar):
        # test calling via command line with args
        csvtempfile = NamedTemporaryFile(suffix='csv')
        stdout = StringIO()
        call_command('reconcile_oclc', '-o', csvtempfile.name, stdout=stdout)
        output = stdout.getvalue()
        assert '0 items to reconcile' in output
        # no file output
        assert not os.stat(csvtempfile.name).st_size
        # no progbar
        mockprogressbar.ProgressBar.assert_not_called()

        # create items that should be ignored (generic, problem, title*)
        Item.objects.create(notes="GENERIC can't identify")
        Item.objects.create(notes="PROBLEM some problematic issue here")
        Item.objects.create(notes="OBSCURE")
        Item.objects.create(title="Plays*")
        stdout = StringIO()
        call_command('reconcile_oclc', '-o', csvtempfile.name, stdout=stdout)
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
        call_command('reconcile_oclc', '-o', csvtempfile.name, stdout=stdout)
        output = stdout.getvalue()
        assert '2 items to reconcile' in output
        # search should be called once for each non-skipped item
        assert mock_oclc_search.call_count == 2

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

        # no progress option respected
        mockprogressbar.reset_mock()
        call_command('reconcile_oclc', '-o', csvtempfile.name,
                    '--no-progress', stdout=stdout)
        mockprogressbar.ProgressBar.assert_not_called()

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

        oclc_info = self.cmd.oclc_search(item)
        # should search on title, author, year
        mock_sru_search.search.assert_called_with(
            title__exact=item.title, author__all=str(person),
            year=item.year)
        # uses first marc record in the response
        marc_record = srwresponse.marc_records[0]
        # can't use assert called with because marc record objects
        # are different, since they are generated dynamically by pymarc
        assert mock_sru_search.get_work_uri.call_count == 1
        args = mock_sru_search.get_work_uri.call_args[0]
        assert isinstance(args[0], pymarc.record.Record)

        # inspect returned details
        assert oclc_info['# matches'] == srwresponse.num_records
        assert oclc_info['OCLC Title'] == marc_record.title()
        assert oclc_info['OCLC Author'] == marc_record.author()
        assert oclc_info['OCLC Date'] == marc_record.pubyear()
        assert oclc_info['OCLC URI'] == oclc_uri(marc_record)
        assert oclc_info['Work URI'] == mock_sru_search.get_work_uri.return_value

        # search does not include missing fields
        # - delete all but title, no events for first known interaction
        creator.delete()
        item.year = None
        oclc_info = self.cmd.oclc_search(item)
        # should search on title only
        mock_sru_search.search.assert_called_with(title__exact=item.title)

        # simulate no year but first known year from events
        with patch.object(Item, 'first_known_interaction', new=datetime.date(1940, 1, 1)):
            oclc_info = self.cmd.oclc_search(item)
            # should search on title and year range
            mock_sru_search.search.assert_called_with(
                title__exact=item.title, year="-1940")

        # simulate no results found
        srwresponse.num_records = 0
        oclc_info = self.cmd.oclc_search(item)
        print(oclc_info)
        # should report 0 matches and nothing else
        assert oclc_info['# matches'] == 0
        assert len(oclc_info) == 1
