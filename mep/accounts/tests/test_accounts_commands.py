import codecs
import os.path
from collections import OrderedDict
from datetime import date, timedelta
from io import StringIO
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import Mock, patch

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import models
from django.test import TestCase

from djiffy.models import Canvas, Manifest

from mep.accounts.management.commands import (
    export_events,
    import_figgy_cards,
    report_timegaps,
    export_addresses,
)
from mep.accounts.models import Account, Borrow, Event, Address, Location
from mep.books.models import Creator, CreatorType
from mep.common.management.export import StreamArray
from mep.common.utils import absolutize_url
from mep.footnotes.models import Bibliography, Footnote
from mep.people.models import Person


class TestReportTimegaps(TestCase):
    def setUp(self):
        self.cmd = report_timegaps.Command()
        self.cmd.stdout = StringIO()

    def test_command_line(self):
        # test calling via command line with args
        csvtempfile = NamedTemporaryFile(suffix="csv")
        stdout = StringIO()
        call_command("report_timegaps", csvtempfile.name, stdout=stdout)

        output = stdout.getvalue()
        # no accounts, nothing done
        assert "Examining 0 accounts with at least two events" in output
        # check that summarize is called
        assert "Found 0 accounts with gaps larger than 6 months" in output

        # alternate gap size honored
        stdout = StringIO()
        call_command("report_timegaps", csvtempfile.name, gap=12, stdout=stdout)
        output = stdout.getvalue()
        assert "Found 0 accounts with gaps larger than 1 year" in output

        csvtempfile.seek(0)
        csv_content = csvtempfile.read().decode()
        assert csv_content.startswith(codecs.BOM_UTF8.decode())
        assert ",".join(self.cmd.csv_header) in csv_content

        # create account and events
        account = Account.objects.create()
        Event.objects.create(
            account=account, start_date=date(1943, 1, 1), end_date=date(1943, 2, 1)
        )
        Event.objects.create(
            account=account, start_date=date(1963, 3, 1), end_date=date(1943, 4, 1)
        )
        call_command("report_timegaps", csvtempfile.name, stdout=stdout)
        csvtempfile.seek(0)
        csv_content = csvtempfile.read().decode()
        # account number/person name included in report
        assert str(account) in csv_content
        # account summary dates included
        assert account.earliest_date().isoformat() in csv_content
        assert account.last_date().isoformat() in csv_content
        # generate gap and report to check inclusion in csv
        gaps = self.cmd.find_gaps(account, timedelta(days=30 * 6))
        max_gap, msg = self.cmd.report_gap_details(gaps)
        # number of gaps, max gap in days, detail all included
        assert str(len(gaps)) in csv_content
        assert str(max_gap) in csv_content
        assert msg in csv_content

        # test verbosity, including skipping a borrow with partial date
        borrow = Borrow.objects.create(account=account)
        borrow.partial_start_date = "1950-01"
        borrow.save()

        stdout = StringIO()
        call_command("report_timegaps", csvtempfile.name, verbosity=2, stdout=stdout)
        output = stdout.getvalue()
        # verbose output includes account summary
        assert str(account) in output
        assert str(account.earliest_date()) in output
        assert str(account.last_date()) in output
        # should not skip partial borrow event if borrows are not included
        assert not "Skipping borrow event with partial dates" in output

        stdout = StringIO()
        call_command(
            "report_timegaps",
            csvtempfile.name,
            verbosity=2,
            stdout=stdout,
            borrows=True,
        )
        output = stdout.getvalue()
        # should note skipped partial borrow event when borrows are included
        assert "Skipping borrow event with partial dates" in output

    def test_format_relativedelta(self):
        assert self.cmd.format_relativedelta(relativedelta(years=1)) == "1 year"
        assert self.cmd.format_relativedelta(relativedelta(years=2)) == "2 years"
        assert (
            self.cmd.format_relativedelta(relativedelta(years=2, months=3))
            == "2 years, 3 months"
        )
        assert (
            self.cmd.format_relativedelta(relativedelta(years=2, months=1))
            == "2 years, 1 month"
        )
        assert (
            self.cmd.format_relativedelta(relativedelta(years=2, months=1))
            == "2 years, 1 month"
        )
        assert (
            self.cmd.format_relativedelta(relativedelta(years=5, days=1))
            == "5 years, 1 day"
        )
        assert (
            self.cmd.format_relativedelta(relativedelta(years=6, days=10))
            == "6 years, 10 days"
        )
        assert (
            self.cmd.format_relativedelta(relativedelta(years=6, months=2, days=10))
            == "6 years, 2 months, 10 days"
        )

    def test_find_gaps(self):
        account = Account.objects.create()

        # no dates, no gaps
        assert self.cmd.find_gaps(account, timedelta(days=30)) == []

        # two events close together, smaller than the gap = still no gaps
        event1 = Event.objects.create(
            account=account, start_date=date(1943, 1, 1), end_date=date(1943, 2, 1)
        )
        event2 = Event.objects.create(
            account=account, start_date=date(1943, 3, 1), end_date=date(1943, 4, 1)
        )
        assert self.cmd.find_gaps(account, timedelta(days=30)) == []

        # if first event end date is not found, start date should be used
        # with gap size of 30 days, this is a gap (1/1 – 3/1)
        event1.end_date = None
        event1.save()
        gaps = self.cmd.find_gaps(account, timedelta(days=30))
        # 1 gap found, returns start/end event objects for the gap
        assert len(gaps) == 1
        assert gaps[0] == (event1, event2)
        # with larger gap size, no gaps should be found
        assert self.cmd.find_gaps(account, timedelta(days=90)) == []

        # if second event start date is not found, end date should be used
        event2.start_date = None
        # 1/1 – 4/1 should be a gap at 30 days
        gaps = self.cmd.find_gaps(account, timedelta(days=30))
        assert len(gaps) == 1
        assert gaps[0] == (event1, event2)

        account.event_set.all().delete()

        # multiple events + gaps
        start_date = date(1922, 1, 1)
        # create multiple objects; start and end date 30 days apart,
        # next event 30 days after previous end
        for i in range(5):
            Event.objects.create(
                account=account,
                start_date=start_date,
                end_date=start_date + timedelta(days=30),
            )
            start_date += timedelta(days=60)

        # no gaps when gapsize is larger than 30
        assert self.cmd.find_gaps(account, timedelta(days=31)) == []
        # 4 gaps when gapsize is less
        gaps = self.cmd.find_gaps(account, timedelta(days=29))
        assert len(gaps) == 4
        events = account.event_set.all()
        assert gaps[0] == (events[0], events[1])
        assert gaps[3] == (events[3], events[4])

        # borrow events with partial dates are currently ignored
        account.event_set.all().delete()
        Event.objects.create(
            account=account, start_date=date(1943, 1, 1), end_date=date(1943, 2, 1)
        )
        borrow = Borrow.objects.create(account=account)
        borrow.partial_start_date = "1950-01"
        borrow.save()
        # gap is significant, but partial dates are skipped
        assert self.cmd.find_gaps(account, timedelta(days=61)) == []

    def test_report_gap_details(self):
        # shouldn't be called with empty gap list normally, but shouldn't error
        max_gap, msg = self.cmd.report_gap_details([])
        assert max_gap == 0
        assert msg == ""

        account = Account.objects.create()
        # add two events to check simple case of gap and message
        event1 = Event.objects.create(
            account=account, start_date=date(1943, 1, 1), end_date=date(1943, 2, 1)
        )
        delta_days = 20
        event2 = Event.objects.create(
            account=account, start_date=event1.end_date + timedelta(days=delta_days)
        )
        max_gap, msg = self.cmd.report_gap_details([(event1, event2)])
        # largest gap reported in days
        assert max_gap == delta_days
        # message includes days and event type
        # (generic events currently display as just 'generic', but there are very few)
        assert msg == "{} days between {}/{} Generic and {}/?? Generic".format(
            delta_days,
            event1.start_date.isoformat(),
            event1.end_date.isoformat(),
            event2.start_date.isoformat(),
        )

        # if multiple events, largest gap is returned
        delta2_days = 25
        event3 = Event.objects.create(
            account=account, start_date=event2.start_date + timedelta(days=delta2_days)
        )
        max_gap, msg = self.cmd.report_gap_details([(event1, event2), (event2, event3)])
        assert max_gap == delta2_days
        # message reports on both gaps
        assert "{} days between".format(delta_days) in msg
        assert "{} days between".format(delta2_days) in msg

        # event type should be reported in message
        borrow = Borrow.objects.create(account=account)
        borrow.partial_start_date = (event3.start_date + timedelta(days=30)).isoformat()
        max_gap, msg = self.cmd.report_gap_details([(event3, borrow)])
        assert "{}/?? Borrow".format(borrow.partial_start_date) in msg


class TestImportFiggyCards(TestCase):
    fixtures = ["messy_footnotes"]

    FIXTURE_DIR = os.path.join("mep", "accounts", "fixtures")

    def setUp(self):
        self.cmd = import_figgy_cards.Command()
        self.cmd.stdout = StringIO()
        self.cmd.script_user = User.objects.get(username=settings.SCRIPT_USERNAME)
        self.cmd.bib_ctype = ContentType.objects.get_for_model(Bibliography).pk
        self.cmd.footnote_ctype = ContentType.objects.get_for_model(Footnote).pk

    def test_clean_footnotes(self):
        self.cmd.clean_footnotes()
        assert Footnote.objects.filter()

        # misspellings fixed
        for error, correction in self.cmd.location_misspellings.items():
            # should be no instance of the error
            assert not Footnote.objects.filter(location__contains=error).exists()
            # should be at least one insstance of the correction
            assert Footnote.objects.filter(location__contains=correction).exists()

        # missing slash between directory and filename
        assert not Footnote.objects.filter(
            location__contains="/d/deslernes000"
        ).exists()
        assert Footnote.objects.filter(location__contains="/d/deslernes/000").exists()

        # double slashes in path fixed
        assert not Footnote.objects.filter(
            location__contains="/825298//c/cornu/"
        ).exists()
        assert Footnote.objects.filter(location__contains="/825298/c/cornu/").exists()

        # number of digits in filename fixed everywhere
        # - OR query because mysql regex doesn't support grouping operator
        assert (
            Footnote.objects.filter(
                models.Q(location__regex=r"\/[0-9]{8}.")
                | models.Q(location__regex=r"\/[0-9]{8}$")
            ).count()
            == Footnote.objects.all().count()
        )

    def test_clean_orphaned_footnotes(self):
        # confirm fixture contains orphans
        assert (
            Footnote.objects.filter(location__contains="pudl")
            .exclude(bibliography__notes__contains=models.F("location"))
            .count()
        )

        # clean first to avoid errors before fixing orphans
        self.cmd.clean_footnotes()
        self.cmd.clean_orphaned_footnotes()
        assert (
            not Footnote.objects.filter(location__contains="pudl")
            .exclude(bibliography__notes__contains=models.F("location"))
            .count()
        )

    @patch("mep.accounts.management.commands.import_figgy_cards.IIIFPresentation")
    def test_migrate_card_bibliography(self, mock_iiifpres):
        # mock actual iiif import
        mock_importer = Mock()
        self.cmd.importer = mock_importer
        test_manifest = Manifest.objects.create()
        mock_importer.import_manifest.return_value = test_manifest
        manifest_uri = "https://exmaple.com/catalog/foo/manifest"
        # simple case - one match
        img_paths = ["r/renaudin/00000001", "r/renaudin/00000002"]
        self.cmd.migrate_card_bibliography(manifest_uri, img_paths)

        mock_iiifpres.from_url.assert_called_with(manifest_uri)
        mock_importer.import_manifest.assert_called_with(
            mock_iiifpres.from_url.return_value, manifest_uri
        )

        # inspect updated bibliography
        renaudin = Bibliography.objects.get(
            bibliographic_note__contains="Paul Renaudin"
        )
        # notes should be empty
        assert not renaudin.notes
        # manifest should be set
        assert renaudin.manifest == test_manifest
        # check that log entry was created
        assert LogEntry.objects.get(object_id=renaudin.pk, action_flag=CHANGE)

        # path occurs in multiple records; test we get the best match
        img_paths = ["p/price/00000006"]
        self.cmd.migrate_card_bibliography(manifest_uri, img_paths)
        brody = Bibliography.objects.get(bibliographic_note__contains="Rachel Brody")
        # notes should be empty
        assert not brody.notes
        # manifest should be set
        assert brody.manifest == test_manifest
        # other record with this image path should be unchanged
        assert Bibliography.objects.filter(notes__contains=img_paths[0]).count() == 1

    def test_migrate_footnotes(self):
        test_manifest = Manifest.objects.create(uri="http://ex.co/manifest/1")
        test_canvas = Canvas.objects.create(
            uri="http://ex.co/manifest/1/canvas/1", manifest=test_manifest, order=1
        )
        pprice = Bibliography.objects.get(bibliographic_note__contains="Phyllis Price")
        pprice.manifest = test_manifest

        canvas_map = {"/p/price/00000006.jp2": test_canvas.uri}
        self.cmd.migrate_footnotes(pprice, canvas_map)
        pprice_footnote = pprice.footnote_set.first()
        # location should be changed
        assert pprice_footnote.location == test_canvas.uri
        # canvas should be associated
        assert pprice_footnote.image == test_canvas
        # log entry should be created
        assert LogEntry.objects.get(object_id=pprice_footnote.id, action_flag=CHANGE)

    @patch(
        "mep.accounts.management.commands.import_figgy_cards.Command.migrate_card_bibliography"
    )
    @patch(
        "mep.accounts.management.commands.import_figgy_cards.Command.migrate_footnotes"
    )
    def test_command_line(self, mock_migrate_footnotes, mock_migrate_card_bib):
        # test calling via command line with args
        stdout = StringIO()
        csvfile = os.path.join(self.FIXTURE_DIR, "test-pudl-to-figgy.csv")
        call_command("import_figgy_cards", csvfile, stdout=stdout)
        output = stdout.getvalue()
        # sanity check output
        assert "Found 17 bibliographies with pudl image paths" in output
        assert "Migration complete" in output
        # numbers unchanged because actual logic was mocked
        assert "Found 17 bibliographies and 12 footnotes with pudl paths" in output
        assert mock_migrate_card_bib.call_count
        assert mock_migrate_footnotes.call_count

        # delete all bibliography records and check that script doesn't do anything
        Bibliography.objects.all().delete()
        mock_migrate_footnotes.reset_mock()
        mock_migrate_card_bib.reset_mock()
        stdout = StringIO()
        csvfile = os.path.join(self.FIXTURE_DIR, "test-pudl-to-figgy.csv")
        call_command("import_figgy_cards", csvfile, stdout=stdout)
        output = stdout.getvalue()
        # should output count but not do anything else
        assert "Found 0 bibliographies with pudl image paths" in output
        assert "Migration complete" not in output
        assert not mock_migrate_card_bib.call_count
        assert not mock_migrate_footnotes.call_count


class TestManifestImportWithRendering:
    @patch("djiffy.importer.ManifestImporter.import_manifest")
    def test_import_manifest(self, mock_import_manifest):
        importer = import_figgy_cards.ManifestImportWithRendering()
        # no rendering - should not error
        mock_manifest = Mock()
        path = "http://example.com/iiif/manifest/1"
        result = importer.import_manifest(mock_manifest, path)
        assert result == mock_import_manifest.return_value
        mock_import_manifest.assert_called_with(mock_manifest, path)

        # if rendering is present, should add to extra data
        mock_manifest.rendering = {"@id": "http://ark.co/1/2/3/4"}
        mock_import_manifest.return_value.extra_data = {}
        result = importer.import_manifest(mock_manifest, path)
        assert "rendering" in result.extra_data
        assert result.extra_data["rendering"] == mock_manifest.rendering


class TestExportEvents(TestCase):
    fixtures = ["test_events"]

    def setUp(self):
        self.cmd = export_events.Command()
        self.cmd.stdout = StringIO()

    def test_get_data(self):
        data = self.cmd.get_data()
        assert isinstance(data, StreamArray)
        assert data.total == Event.objects.count()
        event_data = list(data)
        assert len(event_data) == Event.objects.count()
        assert isinstance(event_data[0], OrderedDict)

    def test_member_info(self):
        # test single member data
        event = Event.objects.filter(account__persons__name__contains="Brue").first()
        person = event.account.persons.first()
        member_info = self.cmd.member_info(event)
        assert member_info["sort_names"][0] == person.sort_name
        assert member_info["names"][0] == person.name
        assert member_info["uris"][0] == absolutize_url(person.get_absolute_url())

        # event with two members; fixture includes Edel joint account
        event = Event.objects.filter(account__persons__name__contains="Edel").first()

        member_info = self.cmd.member_info(event)
        # each field should have two values
        for field in ("sort_names", "names", "uris"):
            assert len(member_info[field]) == 2

        # test event with account but no person
        nomember = Event.objects.filter(account__persons__isnull=True).first()
        assert not self.cmd.member_info(nomember)

    def test_subscription_info(self):
        # get a subscription with no subcategory and both dates
        event = Event.objects.filter(
            subscription__isnull=False,
            start_date__isnull=False,
            end_date__isnull=False,
            subscription__category__isnull=True,
        ).first()
        subs = event.subscription
        info = self.cmd.subscription_info(event)
        assert info["price_paid"] == "%.2f" % subs.price_paid
        # test event has no deposit amount
        assert "deposit" not in info
        assert info["duration"] == subs.readable_duration()
        assert info["duration_days"] == subs.duration
        assert info["volumes"] == subs.volumes
        assert "category" not in info
        # fixture has no purchase date
        assert "purchase_date" not in info

        # add partial purchase date to test
        event.subscription.partial_purchase_date = "1920-05"
        info = self.cmd.subscription_info(event)
        assert info["purchase_date"] == "1920-05"

        # category subtype
        event = Event.objects.filter(subscription__category__isnull=False).first()
        info = self.cmd.subscription_info(event)
        assert info["category"] == event.subscription.category.name

        # missing dates = no duration
        event = Event.objects.filter(
            subscription__isnull=False, end_date__isnull=True
        ).first()
        info = self.cmd.subscription_info(event)
        assert "duration" not in info
        assert "duration_days" not in info

        # non-subscription
        event = Event.objects.filter(subscription__isnull=True).first()
        assert not self.cmd.subscription_info(event)

    def test_borrow_info(self):
        # get a borrow event with both dates
        event = Event.objects.filter(
            borrow__isnull=False, start_date__isnull=False, end_date__isnull=False
        ).first()
        info = self.cmd.get_object_data(event)
        assert info["borrow"]["status"] == event.borrow.get_item_status_display()
        assert info["borrow"]["duration_days"] == event.calculate_duration()

    def test_item_data(self):
        # with work uri and notes
        event = (
            Event.objects.filter(work__isnull=False, edition__isnull=True)
            .exclude(work__uri="")
            .exclude(work__public_notes="")
            .first()
        )
        info = self.cmd.item_info(event)
        assert info["title"] == event.work.title
        assert info["uri"] == absolutize_url(event.work.get_absolute_url())
        assert "work_uri" not in info  # no longer included
        assert "authors" not in info  # not on this record
        assert info["year"] == event.work.year
        assert info["notes"] == event.work.public_notes
        assert "volume" not in info

        # without work uri and notes
        event = Event.objects.filter(
            work__isnull=False, work__uri="", work__public_notes=""
        ).first()
        info = self.cmd.item_info(event)
        assert "work_uri" not in info
        assert "notes" not in info

        # event with known edition
        event = Event.objects.filter(edition__isnull=False).first()
        info = self.cmd.item_info(event)
        assert info["volume"] == event.edition.display_text()

        # no work, no item data
        event = Event.objects.filter(work__isnull=True).first()
        assert not self.cmd.item_info(event)

        # work with author
        event = Event.objects.filter(work__isnull=False).first()
        author1 = Person.objects.create(name="Smith", slug="s")
        author2 = Person.objects.create(name="Jones", slug="j")
        author_type = CreatorType.objects.get(name="Author")
        Creator.objects.create(
            creator_type=author_type, person=author1, work=event.work
        )
        Creator.objects.create(
            creator_type=author_type, person=author2, work=event.work
        )

        info = self.cmd.item_info(event)
        assert info["authors"] == [a.sort_name for a in event.work.authors]

    def test_source_info(self):
        # footnote
        event = Event.objects.filter(footnotes__isnull=False).first()
        footnote = event.footnotes.first()
        info = self.cmd.source_info(footnote)
        assert info["citation"] == footnote.bibliography.bibliographic_note
        assert info["manifest"] == footnote.bibliography.manifest.uri
        assert info["image"] == str(footnote.image.image)
        assert info["type"] == footnote.bibliography.source_type.name

    def test_get_object_data(self):
        # get a subscription with no subcategory and both dates
        event = Event.objects.filter(
            subscription__isnull=False,
            start_date__isnull=False,
            end_date__isnull=False,
            subscription__category__isnull=True,
        ).first()

        data = self.cmd.get_object_data(event)
        assert data["event_type"] == event.event_label
        assert data["currency"] == "FRF"
        assert "member" in data
        assert "subscription" in data

        # test separate payment event includes subscription info
        sub = event.subscription
        sub.subtype = "oth"
        sub.save()
        data = self.cmd.get_object_data(sub.event_ptr)
        assert "subscription" in data

    def test_get_object_data_footnotes(self):
        # get an event from the fixture with a footnote
        event = Event.objects.filter(footnotes__isnull=False).first()
        # add a second footnote (just copy the same bibliography)
        fn1 = event.footnotes.first()
        event.footnotes.create(bibliography=fn1.bibliography)
        data = self.cmd.get_object_data(event)
        # both should be included
        assert len(data["source"]) == 2

    def test_command_line(self):
        # test calling via command line with args
        tempdir = TemporaryDirectory()
        stdout = StringIO()
        call_command("export_events", "-d", tempdir.name, stdout=stdout)
        output = stdout.getvalue()
        assert "Exporting JSON and CSV" in output
        assert os.path.exists(os.path.join(tempdir.name, "events.json"))
        assert os.path.exists(os.path.join(tempdir.name, "events.csv"))

        with patch(
            "mep.accounts.management.commands.export_events"
            + ".Command.get_object_data"
        ) as mock_get_obj_data:
            mock_get_obj_data.return_value = {"event_type": "test"}
            call_command("export_events", "-d", tempdir.name, "-m", 2, stdout=stdout)
            # 2 objects (once each)
            assert mock_get_obj_data.call_count == 2


class TestExportAddresses(TestCase):
    fixtures = ["sample_people"]

    def setUp(self):
        self.cmd = export_addresses.Command()
        self.cmd.stdout = StringIO()

    def test_get_queryset(self):
        # queryset should only include library members
        member = Person.objects.get(pk=189)  # francisque gay, member
        location = Location.objects.get(pk=213)
        address = Address.objects.get(pk=236)
        addresses = self.cmd.get_queryset()
        assert address in set(addresses)
        assert address.location == location
        assert member in set(address.account.persons.all())

    def test_csv_fields(self):
        self.cmd.include_dates = True
        assert self.cmd.csv_fields == self.cmd._csv_fields
        self.cmd.include_dates = False
        assert len(self.cmd.csv_fields) != len(self.cmd._csv_fields)
        assert "start_date" not in self.cmd.csv_fields
        assert "end_date" not in self.cmd.csv_fields

    def test_get_object_data(self):
        # fetch some example people from fixture & call get_object_data
        address = Address.objects.get(pk=236)
        # with dates included
        self.cmd.include_dates = True
        gay_data = self.cmd.get_object_data(address)
        # check some basic data

        # slug is 'gay' in sample_people, 'gay-francisque' in db
        assert gay_data["member"]["ids"] == ["gay"]
        assert gay_data["member"]["uris"] == ["https://example.com/members/gay/"]

        # check addresses & coordinates
        assert "3 Rue Garancière" == gay_data["street_address"]
        assert "Paris" == gay_data["city"]
        assert "France" == gay_data["country"]
        assert 48.85101 == gay_data["latitude"]
        assert 2.33590 == gay_data["longitude"]
        assert "75006" == gay_data["postal_code"]
        assert 6 == gay_data["arrondissement"]
        assert gay_data["start_date"] == "1919-01-01"
        assert gay_data["start_date"] == "1919-01-01"
        assert gay_data["end_date"] == "1930-01-01"
        assert gay_data["care_of_person_id"] == "hemingway"

        # without dates
        self.cmd.include_dates = False
        gay_data = self.cmd.get_object_data(address)
        # doesn't include dates
        assert "start_date" not in gay_data
        assert "end_date" not in gay_data
        # does include other data
        assert gay_data["member"]["ids"] == ["gay"]
        assert gay_data["member"]["uris"] == ["https://example.com/members/gay/"]
        assert gay_data["care_of_person_id"] == "hemingway"
