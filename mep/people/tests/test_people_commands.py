import datetime
from io import StringIO
from django.test import TestCase

from mep.accounts.models import Event
from mep.people.management.commands import export_members, export_creators
from mep.people.models import Person


class TestExportMembers(TestCase):
    fixtures = ["sample_people"]

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
        gay = Person.objects.get(name="Francisque Gay")
        hemingway = Person.objects.get(name="Ernest Hemingway")
        gay_data = self.cmd.get_object_data(gay)
        hemingway_data = self.cmd.get_object_data(hemingway)

        # check some basic data

        # slug is 'gay' in sample_people, 'gay-francisque' in db
        assert gay_data["id"] == "gay"
        assert gay_data["name"] == "Francisque Gay"
        assert gay_data["gender"] == "Male"
        assert gay_data["birth_year"] == 1885

        # slug is 'hemingway' in sample_people, 'hemingway-ernest' in db
        assert hemingway_data["id"] == "hemingway"
        assert hemingway_data["sort_name"] == "Hemingway, Ernest"
        assert hemingway_data["death_year"] == 1961
        assert "title" not in hemingway_data  # empty fields not present
        # fixture has no events, so no years are set
        assert hemingway_data["membership_years"] == []

        # check nationalities
        assert "France" in gay_data["nationalities"]
        assert "United States" in hemingway_data["nationalities"]

        # check viaf & wikipedia urls
        assert (
            hemingway_data["wikipedia_url"]
            == "https://en.wikipedia.org/wiki/Ernest_Hemingway"
        )
        assert gay_data["viaf_url"] == "http://viaf.org/viaf/9857613"

        # check addresses & coordinates
        assert "3 Rue Garancière, Paris" in gay_data["addresses"]
        assert "48.85101, 2.33590" in gay_data["coordinates"]
        assert "75006" in gay_data["postal_codes"]
        assert 6 in gay_data["arrondissements"]

        assert gay_data["updated"] == gay.updated_at.isoformat()
        assert hemingway_data["updated"] == hemingway.updated_at.isoformat()

        # add events to check membership years
        account = gay.account_set.first()
        Event.objects.create(
            account=account,
            start_date=datetime.date(1920, 5, 1),
            end_date=datetime.date(1921, 2, 1),
        )
        Event.objects.create(account=account, start_date=datetime.date(1935, 5, 1))
        gay_data = self.cmd.get_object_data(gay)
        assert gay_data["membership_years"] == [1920, 1921, 1935]

    def test_get_object_data_no_coords(self):
        # handle addresses without coordinates
        gay = Person.objects.get(name="Francisque Gay")
        addr = gay.account_set.first().locations.first()
        addr.longitude = None
        addr.latitude = None
        addr.save()
        gay_data = self.cmd.get_object_data(gay)
        assert "" in gay_data["coordinates"]


class TestExportCreators(TestCase):
    fixtures = ["sample_people"]

    def setUp(self):
        self.cmd = export_creators.Command()
        self.cmd.stdout = StringIO()

    def test_get_queryset(self):
        # queryset should only include library members
        member = Person.objects.get(pk=189)  # francisque gay, member
        author = Person.objects.get(pk=7152)  # aeschylus, non-member
        qs = self.cmd.get_queryset()
        assert author in qs
        assert member not in qs

    def test_get_object_data(self):
        # fetch some example people from fixture & call get_object_data
        aeschylus = Person.objects.get(name="Aeschylus")
        hemingway = Person.objects.get(name="Ernest Hemingway")
        aeschylus_data = self.cmd.get_object_data(aeschylus)
        hemingway_data = self.cmd.get_object_data(hemingway)

        # check some basic data
        assert aeschylus_data["id"] == "aeschylus"
        assert aeschylus_data["name"] == "Aeschylus"
        assert aeschylus_data["gender"] == "Male"
        assert aeschylus_data.get("birth_year") == None

        assert hemingway_data["id"] == "hemingway"
        assert hemingway_data["sort_name"] == "Hemingway, Ernest"
        assert hemingway_data["death_year"] == 1961
        assert "title" not in hemingway_data  # empty fields not present
        # fixture has no events, so no years are set

        # check nationalities
        assert "Ancient Greece" in aeschylus_data["nationalities"]
        assert "United States" in hemingway_data["nationalities"]

        # check viaf & wikipedia urls
        assert (
            hemingway_data["wikipedia_url"]
            == "https://en.wikipedia.org/wiki/Ernest_Hemingway"
        )
        assert hemingway_data["viaf_url"] == "http://viaf.org/viaf/97006051"
