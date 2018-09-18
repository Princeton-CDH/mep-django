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
        return True
        # get the csv export and inspect the response
        # response = self.client.get(reverse('books:items-csv'))
        # assert response.status_code == 200
        # assert response['content-type'] == 'text/csv'
        # content_disposition = response['content-disposition']
        # assert content_disposition.startswith('attachment; filename="')
        # assert 'mep-items-' in content_disposition
        # assert content_disposition.endswith('.csv"')
        # assert now().strftime('%Y%m%d') in content_disposition
        # assert re.search(r'\d{8}T\d{2}:\d{2}:\d{2}', content_disposition)

        # # read content as csv and inspect
        # content = b''.join(response.streaming_content).decode()
        # csvreader = csv.reader(StringIO(content))
        # rows = [row for row in csvreader]
        # items = Item.objects.order_by('id').all()
        # # check for header row
        # assert rows[0] == ItemCSV.header_row
        # # check for expected number of records - header + one row for each work
        # assert len(rows) == items.count() + 1
        # # check expected data in CSV output
        # for item, item_data in zip(items, rows[1:]):
        #     assert str(item.id) in item_data
        #     assert reverse('admin:books_item_change', args=[item.id]) in item_data
        #     assert item.title in item_data
        #     if item.year:
        #         assert str(item.year) in item_data
        #     assert item.uri in item_data
        #     if item.mep_id:
        #         assert item.mep_id in item_data
        #     assert item.notes in item_data
        #     for auth in item.authors:
        #         assert str(auth) in item_data
        #     # no None for empty fields
        #     assert 'None' not in item_data