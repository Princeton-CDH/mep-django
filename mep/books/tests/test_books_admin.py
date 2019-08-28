from unittest.mock import Mock, patch

from django.contrib import admin
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from mep.accounts.models import Account, Borrow, Purchase
from mep.books.admin import WorkAdmin
from mep.books.models import Work


class TestWorkAdmin(TestCase):
    fixtures = ['sample_works']

    @classmethod
    def setUpTestData(cls):
        cls.work_admin = WorkAdmin(model=Work, admin_site=admin.site)
        cls.francisque_gay = Account.objects.get(pk=4852)  # account of library member Francisque Gay
        cls.kreuzer_sonata = Work.objects.get(pk=3)  # book 'The Kreutzer Sonata' by Leo Tolstoy
        cls.exit_eliza = Work.objects.get(pk=1)  # book 'Exit Eliza' by Barry Pain

    def test_get_queryset(self):
        # make a request to the admin and check that the queryset is annotated
        qs = self.work_admin.get_queryset(
            self.client.get(reverse('admin:books_work_changelist')).request
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
            self.client.get(reverse('admin:books_work_changelist')).request
        )
        assert qs.get(pk=self.kreuzer_sonata.id).event__borrow__count == 1
        assert qs.get(pk=self.exit_eliza.id).event__borrow__count == 2

    def test_borrows(self):
        # get items via itemadmin queryset with borrow count annotation
        rqst = self.client.get(reverse('admin:books_work_changelist')).request
        work_queryset = self.work_admin.get_queryset(rqst)
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        # store the URLs that the borrow count links should point to
        kreuzer_sonata_link = (
            reverse('admin:accounts_borrow_changelist') +
            '?work__id__exact=%s' % self.kreuzer_sonata.id)
        exit_eliza_link = (
            reverse('admin:accounts_borrow_changelist') +
            '?work__id__exact=%s' % self.exit_eliza.id)
        # check that event count is rendered as a link with zero events
        assert self.work_admin.borrows(kreuzer_sonata_annotated) == \
            '<a href="%s" target="_blank">0</a>' % kreuzer_sonata_link
        assert self.work_admin.borrows(exit_eliza_annotated) == \
            '<a href="%s" target="_blank">0</a>' % exit_eliza_link
        # francisque borrows "the kreutzer sonata" once
        Borrow(work=self.kreuzer_sonata, account=self.francisque_gay).save()
        # francisque borrows "exit eliza" twice
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        # check that the borrow counts inside the links are updated
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        assert self.work_admin.borrows(kreuzer_sonata_annotated) == \
            '<a href="%s" target="_blank">1</a>' % kreuzer_sonata_link
        assert self.work_admin.borrows(exit_eliza_annotated) == \
            '<a href="%s" target="_blank">2</a>' % exit_eliza_link

    def test_events(self):
        # get items via itemadmin queryset with event count annotation
        rqst = self.client.get(reverse('admin:books_work_changelist')).request
        work_queryset = self.work_admin.get_queryset(rqst)
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        # store the URLs that the event count links should point to
        kreuzer_sonata_link = (
            reverse('admin:accounts_event_changelist') +
            '?work__id__exact=%s' % self.kreuzer_sonata.id)
        exit_eliza_link = (
            reverse('admin:accounts_event_changelist') +
            '?work__id__exact=%s' % self.exit_eliza.id)

        # check that event count is rendered as a link with zero
        assert self.work_admin.events(kreuzer_sonata_annotated) == \
            '<a href="%s" target="_blank">0</a>' % kreuzer_sonata_link
        assert self.work_admin.events(exit_eliza_annotated) == \
            '<a href="%s" target="_blank">0</a>' % exit_eliza_link
        # francisque borrows "the kreutzer sonata" once
        Borrow(work=self.kreuzer_sonata, account=self.francisque_gay).save()
        # francisque borrows "exit eliza" once & purchases once
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        Purchase(work=self.exit_eliza, account=self.francisque_gay).save()
        # check that the borrow counts inside the links are updated
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        assert self.work_admin.events(kreuzer_sonata_annotated) == \
            '<a href="%s" target="_blank">1</a>' % kreuzer_sonata_link
        assert self.work_admin.events(exit_eliza_annotated) == \
            '<a href="%s" target="_blank">2</a>' % exit_eliza_link

    def test_purchases(self):
        # get items via itemadmin queryset with purchase count annotation
        rqst = self.client.get(reverse('admin:books_work_changelist')).request
        work_queryset = self.work_admin.get_queryset(rqst)
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        # store the URLs that the event count links should point to
        kreuzer_sonata_link = (
            reverse('admin:accounts_purchase_changelist') +
            '?work__id__exact=%s' % self.kreuzer_sonata.id)
        exit_eliza_link = (
            reverse('admin:accounts_purchase_changelist') +
            '?work__id__exact=%s' % self.exit_eliza.id)

        # check that purchase count is rendered as a link with zero
        assert self.work_admin.purchases(kreuzer_sonata_annotated) == \
            '<a href="%s" target="_blank">0</a>' % kreuzer_sonata_link
        assert self.work_admin.purchases(exit_eliza_annotated) == \
            '<a href="%s" target="_blank">0</a>' % exit_eliza_link
        # francisque borrows "the kreutzer sonata" once
        Purchase(work=self.kreuzer_sonata, account=self.francisque_gay).save()
        # francisque borrows "exit eliza" once & purchases once
        Borrow(work=self.exit_eliza, account=self.francisque_gay).save()
        Purchase(work=self.exit_eliza, account=self.francisque_gay).save()
        # check that the purchase counts inside the links are updated
        kreuzer_sonata_annotated = work_queryset.get(pk=self.kreuzer_sonata.pk)
        exit_eliza_annotated = work_queryset.get(pk=self.exit_eliza.pk)
        assert self.work_admin.purchases(kreuzer_sonata_annotated) == \
            '<a href="%s" target="_blank">1</a>' % kreuzer_sonata_link
        assert self.work_admin.purchases(exit_eliza_annotated) == \
            '<a href="%s" target="_blank">1</a>' % exit_eliza_link

    def test_tabulate_queryset(self):
        items = Work.objects.order_by('id').all()

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
            for event_count in ('event_count', 'borrow_count',
                                'purchase_count'):
                assert getattr(item, event_count) in item_data

    @patch('mep.books.admin.export_to_csv_response')
    def test_export_csv(self, mock_export_to_csv_response):
        with patch.object(self.work_admin, 'tabulate_queryset') as tabulate_queryset:
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
            assert csvfilename.endswith('.csv')
            assert csvfilename.startswith('mep-works')
            # should include current date
            assert now().strftime('%Y%m%d') in csvfilename
            headers = export_args[1]
            # should use verbose name from db model field
            assert 'MEP ID' in headers
            # or verbose name for property
            assert 'Admin Link' in headers
            # verbose name for event counts
            assert 'Events' in headers
            assert 'Borrows' in headers
