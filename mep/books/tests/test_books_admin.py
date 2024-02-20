import datetime
import time
from unittest.mock import Mock, patch
from io import StringIO
import csv
import os
import random
import tempfile

from django.apps import apps
from django.contrib import admin
from django.db.models.query import EmptyQuerySet
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now
import pytest

from mep.accounts.models import Account, Borrow, Purchase
from mep.accounts.partial_date import DatePrecision
from mep.books.admin import (
    EditionForm,
    WorkAdmin,
    WorkAdminImportExport,
    WORK_IMPORT_COLUMNS,
    WORK_IMPORT_EXPORT_COLUMNS,
)
from mep.books.models import Edition, Work
import uuid


class TestWorkAdmin(TestCase):
    fixtures = ["sample_works"]

    def setUp(self):
        User = apps.get_model("auth", "User")
        # script user needed for log entry logic
        # store the password to login later
        password = str(uuid.uuid4())
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@admin.com", password
        )
        self.client = Client()
        # You'll need to log him in before you can send requests through the client
        self.client.login(username=self.admin_user.username, password=password)
        self.url_import = reverse("admin:books_work_import")
        self.url_process_import = reverse("admin:books_work_process_import")
        self.url_export = reverse("admin:books_work_export")

    @classmethod
    def setUpClass(cls):
        # doesn't support deep copy so must be set here instead of testdata
        cls.work_admin = WorkAdmin(model=Work, admin_site=admin.site)
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.francisque_gay = Account.objects.get(
            pk=4852
        )  # account of library member Francisque Gay
        cls.kreuzer_sonata = Work.objects.get(
            pk=3
        )  # book 'The Kreutzer Sonata' by Leo Tolstoy
        cls.exit_eliza = Work.objects.get(pk=1)  # book 'Exit Eliza' by Barry Pain

    def test_get_queryset(self):
        # make a request to the admin and check that the queryset is annotated
        qs = self.work_admin.get_queryset(
            self.client.get(reverse("admin:books_work_changelist")).request
        )
        # with no borrows, borrow count annotations in queryset should be zero
        for item in qs:
            assert item.event__borrow__count == 0
        # francisque borrows "the kreutzer sonata" once
        Borrow(work=self.kreuzer_sonata, account=self.francisque_gay).save()
        # francisque borrows "exit eliza" twice
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        # make another request and check that borrows are annotated correctly
        qs = self.work_admin.get_queryset(
            self.client.get(reverse("admin:books_work_changelist")).request
        )
        assert qs.get(pk=self.kreuzer_sonata.id).event__borrow__count == 1
        assert qs.get(pk=self.exit_eliza.id).event__borrow__count == 2

    def test_borrows(self):
        # get items via itemadmin queryset with borrow count annotation
        rqst = self.client.get(reverse("admin:books_work_changelist")).request
        work_queryset = self.work_admin.get_queryset(rqst)
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        # store the URLs that the borrow count links should point to
        kreuzer_sonata_link = (
            reverse("admin:accounts_borrow_changelist")
            + "?work__id__exact=%s" % self.kreuzer_sonata.id
        )
        exit_eliza_link = (
            reverse("admin:accounts_borrow_changelist")
            + "?work__id__exact=%s" % self.exit_eliza.id
        )
        # check that event count is rendered as a link with zero events
        assert (
            self.work_admin.borrows(kreuzer_sonata_annotated)
            == '<a href="%s" target="_blank">0</a>' % kreuzer_sonata_link
        )
        assert (
            self.work_admin.borrows(exit_eliza_annotated)
            == '<a href="%s" target="_blank">0</a>' % exit_eliza_link
        )
        # francisque borrows "the kreutzer sonata" once
        Borrow(work=self.kreuzer_sonata, account=self.francisque_gay).save()
        # francisque borrows "exit eliza" twice
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        # check that the borrow counts inside the links are updated
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        assert (
            self.work_admin.borrows(kreuzer_sonata_annotated)
            == '<a href="%s" target="_blank">1</a>' % kreuzer_sonata_link
        )
        assert (
            self.work_admin.borrows(exit_eliza_annotated)
            == '<a href="%s" target="_blank">2</a>' % exit_eliza_link
        )

    def test_events(self):
        # get items via itemadmin queryset with event count annotation
        rqst = self.client.get(reverse("admin:books_work_changelist")).request
        work_queryset = self.work_admin.get_queryset(rqst)
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        # store the URLs that the event count links should point to
        kreuzer_sonata_link = (
            reverse("admin:accounts_event_changelist")
            + "?work__id__exact=%s" % self.kreuzer_sonata.id
        )
        exit_eliza_link = (
            reverse("admin:accounts_event_changelist")
            + "?work__id__exact=%s" % self.exit_eliza.id
        )

        # check that event count is rendered as a link with zero
        assert (
            self.work_admin.events(kreuzer_sonata_annotated)
            == '<a href="%s" target="_blank">0</a>' % kreuzer_sonata_link
        )
        assert (
            self.work_admin.events(exit_eliza_annotated)
            == '<a href="%s" target="_blank">0</a>' % exit_eliza_link
        )
        # francisque borrows "the kreutzer sonata" once
        Borrow(work=self.kreuzer_sonata, account=self.francisque_gay).save()
        # francisque borrows "exit eliza" once & purchases once
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        Purchase(work=self.exit_eliza, account=self.francisque_gay).save()
        # check that the borrow counts inside the links are updated
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        assert (
            self.work_admin.events(kreuzer_sonata_annotated)
            == '<a href="%s" target="_blank">1</a>' % kreuzer_sonata_link
        )
        assert (
            self.work_admin.events(exit_eliza_annotated)
            == '<a href="%s" target="_blank">2</a>' % exit_eliza_link
        )

    def test_purchases(self):
        # get items via itemadmin queryset with purchase count annotation
        rqst = self.client.get(reverse("admin:books_work_changelist")).request
        work_queryset = self.work_admin.get_queryset(rqst)
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        # store the URLs that the event count links should point to
        kreuzer_sonata_link = (
            reverse("admin:accounts_purchase_changelist")
            + "?work__id__exact=%s" % self.kreuzer_sonata.id
        )
        exit_eliza_link = (
            reverse("admin:accounts_purchase_changelist")
            + "?work__id__exact=%s" % self.exit_eliza.id
        )

        # check that purchase count is rendered as a link with zero
        assert (
            self.work_admin.purchases(kreuzer_sonata_annotated)
            == '<a href="%s" target="_blank">0</a>' % kreuzer_sonata_link
        )
        assert (
            self.work_admin.purchases(exit_eliza_annotated)
            == '<a href="%s" target="_blank">0</a>' % exit_eliza_link
        )
        # francisque borrows "the kreutzer sonata" once
        Purchase(work=self.kreuzer_sonata, account=self.francisque_gay).save()
        # francisque borrows "exit eliza" once & purchases once
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        Purchase(work=self.exit_eliza, account=self.francisque_gay).save()
        # check that the purchase counts inside the links are updated
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        assert (
            self.work_admin.purchases(kreuzer_sonata_annotated)
            == '<a href="%s" target="_blank">1</a>' % kreuzer_sonata_link
        )
        assert (
            self.work_admin.purchases(exit_eliza_annotated)
            == '<a href="%s" target="_blank">1</a>' % exit_eliza_link
        )

    def test_tabulate_queryset(self):
        items = Work.objects.order_by("id").all()

        # create some events to check event counts
        # kreuzer_sonata = items.get(pk=self.kreuzer_sonata.pk)
        # exit_eliza = items.get(pk=self.exit_eliza.pk)
        # francisque borrows "the kreutzer sonata" once
        Borrow(work=self.kreuzer_sonata, account=self.francisque_gay).save()
        # francisque borrows "exit eliza" once & purchases once
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        Purchase(work=self.exit_eliza, account=self.francisque_gay).save()

        # test that tabular data matches queryset data
        for item, item_data in zip(items, self.work_admin.tabulate_queryset(items)):
            # test some properties
            assert item.title in item_data
            assert item.year in item_data
            # test some methods
            assert item.author_list() in item_data
            assert item.admin_url() in item_data
            # test event counts from annotation
            for event_count in ("event_count", "borrow_count", "purchase_count"):
                assert getattr(item, event_count) in item_data

    @patch("mep.books.admin.export_to_csv_response")
    def test_export_csv(self, mock_export_to_csv_response):
        with patch.object(self.work_admin, "tabulate_queryset") as tabulate_queryset:
            # if no queryset provided, should use default queryset
            items = self.work_admin.get_queryset(Mock())
            self.work_admin.export_to_csv(Mock())
            assert tabulate_queryset.called_once_with(items)
            # otherwise should respect the provided queryset
            first_item = Work.objects.all()[:0]
            self.work_admin.export_to_csv(Mock(), first_item)
            assert tabulate_queryset.called_once_with(first_item)

            export_args, export_kwargs = mock_export_to_csv_response.call_args
            # first arg is filename
            csvfilename = export_args[0]
            assert csvfilename.endswith(".csv")
            assert csvfilename.startswith("mep-works")
            # should include current date
            assert now().strftime("%Y%m%d") in csvfilename
            headers = export_args[1]
            # should use verbose name from db model field
            assert "MEP ID" in headers
            # or verbose name for property
            assert "Admin Link" in headers
            # verbose name for event counts
            assert "Events" in headers
            assert "Borrows" in headers
            assert "Purchases" in headers

    def test_get_search_results(self):
        # index fixture data in solr
        Work.index_items(Work.objects.all())
        time.sleep(1)

        queryset, needs_distinct = self.work_admin.get_search_results(
            Mock(), Work.objects.all(), "bogus"
        )
        assert not queryset.count()
        assert not needs_distinct
        assert isinstance(queryset, EmptyQuerySet)

        queryset, needs_distinct = self.work_admin.get_search_results(
            Mock(), Work.objects.all(), "fairy tales"
        )
        assert queryset.count() == 1
        assert isinstance(queryset.first(), Work)

        # empty search term should return all records
        queryset, needs_distinct = self.work_admin.get_search_results(
            Mock(), Work.objects.all(), ""
        )
        assert queryset.count() == Work.objects.all().count()

    def _djangoimportexport_do_export_post(self, file_format=0):
        """
        Send POST request to exporting url, and return HTTP response object
        """
        response = self.client.post(self.url_export, {"file_format": str(file_format)})
        return response

    def test_djangoimportexport_export(self):
        ### test can get page
        response = self.client.get(self.url_export)
        self.assertEqual(response.status_code, 200)

        ### test can post to page and get csv data back
        date_str = now().strftime("%Y-%m-%d")
        response = self._djangoimportexport_do_export_post(file_format=0)  # csv

        # test response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("Content-Disposition"))
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="Work-{}.csv"'.format(date_str),
        )

        # test csv as binary string response
        lines = response.content.splitlines()
        assert len(lines) > 0, "no header returned"
        self.assertEqual(
            ",".join(WORK_IMPORT_EXPORT_COLUMNS).encode(),
            lines[0],
        )

        # test csv via csv reader
        f = StringIO(response.content.decode())
        reader = csv.DictReader(f, delimiter=",")
        rows = list(reader)
        works = Work.objects.all()

        # test num lines, should be a row per work
        assert len(rows) == len(works)

        # test values by row
        work_admin = WorkAdminImportExport(model=Work, admin_site=admin.site)
        export_class = work_admin.get_export_resource_classes()[0]
        exporter = export_class()

        def getstr(work, attr, default=""):
            field = exporter.fields[attr]
            res = exporter.export_field(field, work)
            return str(res) if res or res == 0 else default

        for work, row in zip(works, rows):
            for attr in WORK_IMPORT_EXPORT_COLUMNS:
                self.assertEqual(getstr(work, attr), row[attr])

    def _djangoimportexport_do_import_post(
        self, url, filename, input_format=0, follow=False
    ):
        """
        Send POST request to import url, with a filename to import,
        and return HTTP response object
        """
        with open(filename, "rb") as f:
            data = {
                "input_format": str(input_format),
                "import_file": f,
            }
            response = self.client.post(url, data, follow=follow)
        return response

    @pytest.mark.last
    def test_djangoimportexport_import(self):
        ### test can get page
        response = self.client.get(self.url_import)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/import_export/import.html")
        self.assertContains(response, 'form action=""')

        tmpfn = "works.csv"
        ## test import with changed data

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_filename = os.path.join(tmpdir, tmpfn)
            # quick export
            response = self._djangoimportexport_do_export_post()
            # modify
            f = StringIO(response.content.decode())
            reader = csv.DictReader(f, delimiter=",")
            rows = list(reader)
            categories = ["Fiction", "Nonfiction", "Drama", "Poetry", "Periodical", ""]
            for row in rows:
                row["categories"] = random.choice(
                    [x for x in categories if x != row["categories"]]
                )
            # save
            with open(csv_filename, "w") as of:
                writer = csv.DictWriter(of, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            # now import
            response = self._djangoimportexport_do_import_post(
                self.url_import, csv_filename
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("result", response.context)
            self.assertFalse(response.context["result"].has_errors())
            self.assertIn("confirm_form", response.context)
            confirm_form = response.context["confirm_form"]

            data = confirm_form.initial
            self.assertEqual(data["original_file_name"], tmpfn)
            response = self.client.post(self.url_process_import, data, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                ("Import finished, with {} new and {} updated {}.").format(
                    0, len(rows), Work._meta.verbose_name_plural
                ),
            )

            assert response.content.count(b'<tr class="grp-row') == len(rows)


class TestEditionForm(TestCase):
    # tests adapted from PartialDateFormMixin tests in account admin tests

    def test_get_initial_for_field(self):
        work = Work.objects.create()
        edition = Edition(work=work, volume=1)
        edition.partial_date = "1901-05"
        form = EditionForm(instance=edition)
        # ensure that partial date is auto-populated correctly
        assert (
            form.get_initial_for_field(form.fields["partial_date"], "partial_date")
            == edition.partial_date
        )
        # shouldn't affect other fields
        assert (
            form.get_initial_for_field(form.fields["volume"], "volume")
            == edition.volume
        )

    def test_validation(self):
        work = Work.objects.create()
        edition = Edition(work=work)
        edition.partial_date = "1901-05"

        # check date validation
        form_data = {"partial_date": "1901-05", "work": work.id}
        form = EditionForm(form_data, instance=edition)
        assert form.is_valid()
        # invalid
        form_data["partial_date"] = "20-20"
        form = EditionForm(form_data, instance=edition)
        assert not form.is_valid()

    def test_clean(self):
        work = Work.objects.create()
        edition = Edition(work=work)

        # a newly created edition should have None for all date values
        assert edition.date is None
        assert edition.date_precision is None
        # fill out some valid partial dates for start and end
        form_data = {"partial_date": "1931-06", "work": work.id}
        form = EditionForm(form_data, instance=edition)
        assert form.is_valid()
        form.clean()
        # dates and precision should get correctly set through the descriptor
        assert edition.date == datetime.date(1931, 6, 1)
        assert edition.date_precision == DatePrecision.year | DatePrecision.month
