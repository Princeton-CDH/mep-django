import json
from unittest.mock import MagicMock, Mock, patch

from django.test import RequestFactory, TestCase
from django.urls import reverse

from mep.accounts.models import Account, Address
from mep.accounts.queryset import AddressSolrQuerySet
from mep.accounts.views import AddressList
from mep.people.models import Location, Person
from mep.people.queryset import PersonSolrQuerySet


class TestAccountsViews(TestCase):

    def test_account_autocomplete(self):
        url = reverse('accounts:autocomplete')
        res = self.client.get(url)

        # getting the view returns 200
        assert res.status_code == 200
        data = res.json()
        # there is a results list in the JSON
        assert 'results' in data
        # it is empty because there are no accounts or query
        assert not data['results']

        # - test search and sort

        # search by pk
        acc1 = Account.objects.create()
        acc2 = Account.objects.create()
        res = self.client.get(url, {'q': acc1.pk})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == 'Account #%s' % acc1.pk

        # search by persons
        pers1 = Person.objects.create(name='Mlle Foo', slug='foo')
        pers2 = Person.objects.create(name='Msr Foo', slug='foo-2')
        acc2.persons.add(pers1, pers2)
        res = self.client.get(url, {'q': 'Mlle'})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == \
            'Account #%s: Mlle Foo, Msr Foo' % acc2.pk

        # search by address
        loc1 = Location.objects.create(street_address='1 Rue St.')
        Address.objects.create(account=acc1, location=loc1)
        res = self.client.get(url, {'q': 'Rue'})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == 'Account #%s: 1 Rue St.' % acc1.pk

        # query can end up listing account more than once
        # note: couldn't actually duplicate the problem here that
        # was happening on the site before adding distinct()
        hemier = Person.objects.create(name='hemingway', mep_id="hemi.er",
                                       slug='hemingway')
        acc3 = Account.objects.create()
        acc3.persons.add(hemier)
        loc2 = Location.objects.create(name='hemingway\'s place')
        Address.objects.create(account=acc3, location=loc2)
        res = self.client.get(url, {'q': 'hem'})
        data = res.json()
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == 'Account #%s: %s' % (acc3.pk, hemier)


class TestAddressListView(TestCase):
    fixtures = ['sample_people']

    def setUp(self):
        self.factory = RequestFactory()
        self.view_url = reverse('accounts:members-addresses')

    @patch('mep.accounts.views.AddressSolrQuerySet', spec=AddressSolrQuerySet)
    def test_get_queryset(self, mock_solrqueryset):
        mock_qs = mock_solrqueryset.return_value
        # simulate fluent interface
        for meth in ['facet_field', 'filter', 'only', 'search', 'also',
                     'raw_query_parameters', 'order_by', 'all']:
            getattr(mock_qs, meth).return_value = mock_qs
        mock_qs.filter_qs = []

        view = AddressList()
        view.request = self.factory.get(self.view_url)

        # returns solr queryset for members
        members = view.get_queryset()
        assert isinstance(members, PersonSolrQuerySet)
        assert isinstance(view.addresses, AddressSolrQuerySet)

        # no filters/search terms
        assert not mock_qs.search.call_count
        assert not mock_qs.raw_query_parameters.call_count
        assert not mock_qs.filter_qs

        # member filter refined
        assert not members.facet_field_list  # no facets
        assert members.search_qs[0].startswith('{!join')
        assert len(members.field_list) == 4    # limited return field list

        # with filter & search term
        view = AddressList()
        view.request = self.factory.get(
            self.view_url, {'has_card': 'on', 'query': 'hemi'})
        members = view.get_queryset()
        mock_qs.search.assert_called_with(
            '{!join from=slug_s to=member_slug_ss v=$name_q}')
        mock_qs.raw_query_parameters.assert_called_with(
            name_q='name_t:(hemi) OR sort_name_t:(hemi) OR name_ngram:(hemi)')
        assert mock_qs.filter_qs[0].startswith(
            '{!join from=slug_s to=member_slug_ss}')

    def test_render_to_response(self):
        view = AddressList()
        view.request = self.factory.get(self.view_url)
        view.object_list = Mock()
        view.object_list.count.return_value = 2
        mock_member_results = [
            {'slug': 'ann', 'name': 'Ann'},
            {'slug': 'jon', 'name': 'Jon'},
        ]
        view.object_list.get_results.return_value = mock_member_results
        view.addresses = MagicMock()
        view.addresses.count.return_value = 3
        response = view.render_to_response(view.request)
        # decode from binary to string then read as json
        data = json.loads(response.content.decode())
        assert data['numFound']['addresses'] == 3
        assert data['numFound']['members'] == 2
        assert 'addresses' in data
        # member data as dict keyed on slug
        assert data['members']['ann'] == mock_member_results[0]
        assert data['members']['jon'] == mock_member_results[1]
