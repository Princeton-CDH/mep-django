import csv
from io import StringIO
from unittest.mock import Mock

from django.test import TestCase
from django.contrib import admin
from django.urls import reverse

from mep.accounts.models import Borrow, Account
from mep.books.admin import ItemAdmin
from mep.books.models import Item


class TestItemAdmin(TestCase):

    def test_get_queryset(self):
        # create a test admin instance - don't think admin_site is actually called?
        item_admin = ItemAdmin(model=Item, admin_site=admin.site)
        # create some test books
        item1 = Item(title='Le foo et le bar', year=1916, mep_id='lfelb')
        item2 = Item(title='Le foo et le bar: le sequel', year=1918, mep_id='lfelbls')
        item1.save()
        item2.save()
        # make a request to the admin and check that the queryset is annotated
        qs = item_admin.get_queryset(
            self.client.get(reverse('admin:books_item_changelist')).request
        )
        # with no borrows, borrow count annotations in queryset should be zero
        for item in qs:
            assert item.borrow__count == 0
        # create a test account and borrow some of the books
        acct = Account()
        acct.save()
        Borrow(item=item1, account=acct).save()
        Borrow(item=item2, account=acct).save()
        Borrow(item=item2, account=acct).save()
        # make another request and check that borrows are annotated correctly
        qs = item_admin.get_queryset(
            self.client.get(reverse('admin:books_item_changelist')).request
        )
        assert qs[0].borrow__count == 1
        assert qs[1].borrow__count == 2

    def test_borrow_count(self):
        # create a test admin instance - don't think admin_site is actually called?
        item_admin = ItemAdmin(model=Item, admin_site=admin.site)
        # create some test books; don't borrow them yet
        item1 = Item(title='Le foo et le bar', year=1916, mep_id='lfelb')
        item2 = Item(title='Le foo et le bar: le sequel', year=1918, mep_id='lfelbls')
        item1.save()
        item2.save()

        # get items via itemadmin queryset with borrow count annotation
        item_admin = ItemAdmin(model=Item, admin_site=admin.site)
        rqst = self.client.get(reverse('admin:books_item_changelist')).request
        item1 = item_admin.get_queryset(rqst).get(pk=item1.pk)
        item2 = item_admin.get_queryset(rqst).get(pk=item2.pk)

        # store the URLs that the borrow count links should point to
        borrows1 = (reverse('admin:accounts_borrow_changelist') +
                    '?item__id__exact=' + str(item1.id))
        borrows2 = (reverse('admin:accounts_borrow_changelist') +
                    '?item__id__exact=' + str(item2.id))
        # check that borrow count is rendered as a link with zero borrows
        assert item_admin.borrow_count(item1) == '<a href="%s" target="_blank">0</a>' % borrows1
        assert item_admin.borrow_count(item2) == '<a href="%s" target="_blank">0</a>' % borrows2
        # create a test account and borrow some of the books
        acct = Account()
        acct.save()
        Borrow(item=item1, account=acct).save()
        Borrow(item=item2, account=acct).save()
        Borrow(item=item2, account=acct).save()
        # check that the borrow counts inside the links are updated
        item1 = item_admin.get_queryset(rqst).get(pk=item1.pk)
        item2 = item_admin.get_queryset(rqst).get(pk=item2.pk)
        assert item_admin.borrow_count(item1) == '<a href="%s" target="_blank">1</a>' % borrows1
        assert item_admin.borrow_count(item2) == '<a href="%s" target="_blank">2</a>' % borrows2

    def test_export_csv(self):
        fixtures = ['sample_items']
        item_admin = ItemAdmin(model=Item, admin_site=admin.site)
        items = Item.objects.order_by('id').all()
        # get the csv and inspect its contents
        response = item_admin.export_to_csv(Mock(), items)
        content = b''.join(response.streaming_content).decode()
        csvreader = csv.reader(StringIO(content))
        rows = [row for row in csvreader]
        # check for header row with custom fields
        assert rows[0] == item_admin.tabular_headers(items)
        # check for expected number of records - header + one row for each work
        assert len(rows) == items.count() + 1
        # check custom fields are in csv data
        for item, item_data in zip(items, rows[1:]):
            # url to item
            assert reverse('admin:books_item_change', args=[item.id]) in item_data
            # item authors
            assert ';'.join([str(auth) for auth in item.authors]) in item_data
