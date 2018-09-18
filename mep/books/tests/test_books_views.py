import csv
from io import StringIO
import re

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import now

from mep.books.models import Item


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
