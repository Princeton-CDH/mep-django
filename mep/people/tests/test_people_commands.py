import datetime
from io import StringIO

from django.test import TestCase

from mep.accounts.models import Event
from mep.people.management.commands import export_members
from mep.people.models import Person


class TestExportMembers(TestCase):
    fixtures = ['sample_people']

    def setUp(self):
        self.cmd = export_members.Command()
        self.cmd.stdout = StringIO()

    def test_get_queryset(self):
        # queryset should only include library members
        member = Person.objects.get(pk=189)  # francisque gay, member
        author = Person.objects.get(pk=7152)  # aeschylus, non-member
        qs = self.cmd.get_queryset()
        assert member in qs
        assert author not in qs

    def test_get_object_data(self):
        # fetch some example people from fixture & call get_object_data
        gay = Person.objects.get(name='Francisque Gay')
        hemingway = Person.objects.get(name='Ernest Hemingway')
        gay_data = self.cmd.get_object_data(gay)
        hemingway_data = self.cmd.get_object_data(hemingway)

        # check some basic data
        assert gay_data['name'] == 'Francisque Gay'
        assert gay_data['gender'] == 'Male'
        assert gay_data['birth_year'] == 1885
        assert hemingway_data['sort_name'] == 'Hemingway, Ernest'
        assert hemingway_data['death_year'] == 1961
        assert 'title' not in hemingway_data   # empty fields not present
        # fixture has no events, so no years are set
        assert hemingway_data['membership_years'] == []

        # check nationalities
        assert 'France' in gay_data['nationalities']
        assert 'United States' in hemingway_data['nationalities']

        # check viaf & wikipedia urls
        assert hemingway_data['wikipedia_url'] == \
            'https://en.wikipedia.org/wiki/Ernest_Hemingway'
        assert gay_data['viaf_url'] == 'http://viaf.org/viaf/9857613'

        # check addresses & coordinates
        assert '3 Rue Garancière, Paris' in gay_data['addresses']
        assert '48.85101, 2.33590' in gay_data['coordinates']

        assert gay_data['updated'] == gay.updated_at.isoformat()
        assert hemingway_data['updated'] == hemingway.updated_at.isoformat()

        # add events to check membership years
        account = gay.account_set.first()
        Event.objects.create(
            account=account, start_date=datetime.date(1920, 5, 1),
            end_date=datetime.date(1921, 2, 1))
        Event.objects.create(
            account=account, start_date=datetime.date(1935, 5, 1))
        gay_data = self.cmd.get_object_data(gay)
        assert gay_data['membership_years'] == [1920, 1921, 1935]
