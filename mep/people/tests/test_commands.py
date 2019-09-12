from io import StringIO
from unittest.mock import patch, Mock

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
import pytest

from mep.people.management.commands import import_personography
from mep.people.models import Person, Location, Country, InfoURL
from mep.people import xml_models


class TestImportPersonography(TestCase):

    def setUp(self):
        self.cmd = import_personography.Command()
        self.cmd.stdout = StringIO()

    @patch('mep.people.management.commands.import_personography.Personography')
    def test_command_line(self, mock_xmlpersonography):
        # test calling via command line with args
        path = '/some/path/to/persons.xml'
        call_command('import_personography', path)
        mock_xmlpersonography.from_file.assert_called_with(path)

    @patch('mep.people.management.commands.import_personography.Personography')
    def test_command(self, mock_xmlpersonography):
        # simulate bad path
        bad_path = '/home/me/not/here'
        mock_xmlpersonography.from_file.side_effect = Exception
        with pytest.raises(CommandError) as excinfo:
            self.cmd.handle(path=bad_path)
        mock_xmlpersonography.from_file.assert_called_with(bad_path)
        assert 'Failed to load' in str(excinfo.value)

        # simulate valid path
        mock_xmlpersonography.from_file.side_effect = None
        mockperson1 = Mock(spec=xml_models.Person)
        mockperson1.is_imported.return_value = False
        mockperson2 = Mock(spec=xml_models.Person)
        mock_xmlpersonography.from_file.return_value.people = [
            mockperson1, mockperson2
        ]
        self.cmd.handle(path='/some/actual/path.xml')
        # not yet imported: should be converted to db record
        mockperson1.to_db_person.assert_called_with()
        # already imported: should not be converted to db record
        mockperson2.to_db_person.assert_not_called()

        output = self.cmd.stdout.getvalue()
        assert 'Found 2 people in XML personography' in output
        # check that summarize is called
        assert '0 people added' in output

    def test_get_totals(self):
        # nothing loaded
        totals = self.cmd.get_totals()
        for model in ['people', 'addresses', 'countries', 'urls']:
            assert model in totals
            assert totals[model] == 0

        # add a few things
        p = Person.objects.create(name='somebody')
        Location.objects.create(city='Paris')
        Country.objects.create(name='[no country]')
        InfoURL.objects.create(person=p, url='http://example.com')

        totals = self.cmd.get_totals()
        for model in ['people', 'addresses', 'countries', 'urls']:
            assert model in totals
            assert totals[model] == 1

    def test_summarize(self):
        empty_totals = self.cmd.get_totals()

        # add a few things
        p = Person.objects.create(name='somebody')
        Person.objects.create(name='somebody else')
        Location.objects.create(city='Paris')
        Country.objects.create(name='[no country]')
        InfoURL.objects.create(person=p, url='http://example.com')

        self.cmd.summarize(empty_totals)
        output = self.cmd.stdout.getvalue()
        expected_text = [
            '2 people added (2 total)',
            '1 addresses added (1 total)',
            '1 countries added (1 total)',
            '1 urls added (1 total)'
        ]
        for txt in expected_text:
            assert txt in output

        new_totals = self.cmd.get_totals()
        # add a few more things
        Person.objects.create(name='another')
        Person.objects.create(name='fourth')
        Country.objects.create(name='Utopia', geonames_id=12345, code='UT')
        # check new summary
        self.cmd.summarize(new_totals)
        output = self.cmd.stdout.getvalue()
        expected_text = [
            '2 people added (4 total)',
            '0 addresses added (1 total)',
            '1 countries added (2 total)',
            '0 urls added (1 total)'
        ]
        for txt in expected_text:
            assert txt in output
