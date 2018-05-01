import csv
from io import StringIO
import re

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import now

from mep.books.models import Item
from mep.books.views import ItemCSV


class TestBooksViews(TestCase):
    fixtures = ['sample_items']

    def setUp(self):
        self.admin_pass = 'password'
        self.admin_user = get_user_model().objects.create_superuser(
            'admin', 'admin@example.com', self.admin_pass)

    def test_item_autocomplete(self):
        # remove fixture items to duplicate previous test conditions
        Item.objects.all().delete()

        url = reverse('books:item-autocomplete')
        res = self.client.get(url)

        # getting the view returns 200
        assert res.status_code == 200
        data = res.json()
        # there is a results list in the JSON
        assert 'results' in data
        # it is empty because there are no accounts or query
        assert not data['results']

        # - test basic search and sort

        # search by title
        item1 = Item.objects.create(title='Poems Two Painters', mep_id='mep:01',
            notes='Author: Knud Merrild')
        item2 = Item.objects.create(title='Collected Poems', mep_id='mep:02')
        res = self.client.get(url, {'q': 'poems'})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 2
        assert data['results'][0]['text'] == item2.title
        assert data['results'][1]['text'] == item1.title

        # search by note text
        res = self.client.get(url, {'q': 'knud'})
        data = res.json()
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == item1.title

        # search by mep id
        res = self.client.get(url, {'q': 'mep:02'})
        data = res.json()
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == item2.title

    def test_items_csv(self):
        # get the csv export and inspect the response
        response = self.client.get(reverse('books:items-csv'))
        assert response.status_code == 200
        assert response['content-type'] == 'text/csv'
        content_disposition = response['content-disposition']
        assert content_disposition.startswith('attachment; filename="')
        assert 'mep-items-' in content_disposition
        assert content_disposition.endswith('.csv"')
        assert now().strftime('%Y%m%d') in content_disposition
        assert re.search(r'\d{8}T\d{2}:\d{2}:\d{2}', content_disposition)

        # read content as csv and inspect
        content = b''.join(response.streaming_content).decode()
        csvreader = csv.reader(StringIO(content))
        rows = [row for row in csvreader]
        items = Item.objects.order_by('id').all()
        # check for header row
        assert rows[0] == ItemCSV.header_row
        # check for expected number of records - header + one row for each work
        assert len(rows) == items.count() + 1
        # check expected data in CSV output
        for item, item_data in zip(items, rows[1:]):
            assert str(item.id) in item_data
            assert reverse('admin:books_item_change', args=[item.id]) in item_data
            assert item.title in item_data
            if item.year:
                assert str(item.year) in item_data
            assert item.uri in item_data
            if item.mep_id:
                assert item.mep_id in item_data
            assert item.notes in item_data
            for auth in item.authors:
                assert str(auth) in item_data
            # no None for empty fields
            assert 'None' not in item_data

    def test_item_admin_changelist(self):
        # log in as admin to access admin site views
        self.client.login(username=self.admin_user.username,
            password=self.admin_pass)
        # get item change list
        response = self.client.get(reverse('admin:books_item_changelist'))
        self.assertContains(response, reverse('books:items-csv'),
            msg_prefix='item change list should include CSV download link')
        self.assertContains(response, 'Download as CSV',
            msg_prefix='item change list should include CSV download button')

        # link should not be on other change lists
        response = self.client.get(reverse('admin:auth_user_changelist'))
        self.assertNotContains(response, reverse('books:items-csv'),
            msg_prefix='item CSV download link should only be on digitized work list')
