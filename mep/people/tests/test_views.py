import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.test import TestCase
from django.urls import reverse

from mep.accounts.models import Account, Subscription, Address
from mep.people.admin import GeoNamesLookupWidget, MapWidget
from mep.people.geonames import GeoNamesAPI
from mep.people.models import Location, Country, Person, Relationship, \
    RelationshipType
from mep.people.views import GeoNamesLookup


class TestPeopleViews(TestCase):

    @patch('mep.people.views.GeoNamesAPI')
    def test_geonames_autocomplete(self, mockgeonamesapi):
        geo_lookup_url = reverse('people:geonames-lookup')
        # abbreviated sample return with fields currently in use
        mock_response = [
            {'name': 'New York City', 'geonameId': 5128581,
             'countryName': 'USA', 'lat': 40.71427, 'lng': -74.00597,
             'countryCode': 'US'}
        ]
        mockgeonamesapi.return_value.search.return_value = mock_response
        # patch in real uri from id logic
        mockgeonamesapi.return_value.uri_from_id = GeoNamesAPI.uri_from_id

        result = self.client.get(geo_lookup_url, {'q': 'new york'})
        assert isinstance(result, JsonResponse)
        assert result.status_code == 200
        mockgeonamesapi.return_value.search.assert_called_with('new york',
            max_rows=50, name_start=True)
        # decode response to inspect
        data = json.loads(result.content.decode('utf-8'))
        # inspect constructed result
        item = data['results'][0]
        assert item['text'] == 'New York City, USA'
        assert item['name'] == 'New York City'
        assert item['lat'] == mock_response[0]['lat']
        assert item['lng'] == mock_response[0]['lng']
        assert item['id'] == \
            GeoNamesAPI.uri_from_id(mock_response[0]['geonameId'])

        # country specific lookup
        country_lookup_url = reverse('people:country-lookup')
        result = self.client.get(country_lookup_url, {'q': 'canada'})
        assert result.status_code == 200
        mockgeonamesapi.return_value.search.assert_called_with('canada',
            feature_class='A', feature_code='PCLI', max_rows=50,
            name_start=True)

    def test_person_autocomplete(self):
        # add a person to search for
        beach = Person.objects.create(name='Sylvia Beach', mep_id='sylv.b')

        pub_autocomplete_url = reverse('people:autocomplete')
        result = self.client.get(pub_autocomplete_url, {'q': 'beach'})
        assert result.status_code == 200
        # decode response to inspect basic formatting and fields
        data = json.loads(result.content.decode('utf-8'))
        text = data['results'][0]['text']
        self.assertInHTML('<strong>Sylvia Beach</strong> sylv.b', text)

        # no match - shouldn't error, just return no results
        result = self.client.get(pub_autocomplete_url, {'q': 'beauvoir'})
        assert result.status_code == 200
        data = json.loads(result.content.decode('utf-8'))
        assert not data['results']

        # add a person and a title
        ms_sylvia = Person.objects.create(name='Sylvia', title='Ms.')

        # should return both wrapped in <strong>
        result = self.client.get(pub_autocomplete_url, {'q': 'sylvia'})
        assert result.status_code == 200
        # decode response to inspect
        data = json.loads(result.content.decode('utf-8'))
        assert len(data['results']) == 2
        assert 'Sylvia Beach' in data['results'][0]['text']
        # detailed check of Ms. Sylvia
        text = data['results'][1]['text']
        self.assertInHTML('<strong>Ms. Sylvia</strong>', text)

        # should select the right person based on mep_id
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.b'})
        assert result.status_code == 200
        # decode response to inspect
        data = json.loads(result.content.decode('utf-8'))
        assert len(data['results']) == 1
        assert 'Sylvia Beach' in data['results'][0]['text']

        # add birth, death dates to beach
        beach.birth_year = 1900
        beach.death_year = 1970
        beach.save()
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.b'})
        # decode response to inspect dates rendered and formatted correctly
        data = json.loads(result.content.decode('utf-8'))
        assert len(data['results']) == 1
        text = data['results'][0]['text']
        expected = '<strong>Sylvia Beach (1900 - 1970)</strong> sylv.b <br />'
        self.assertInHTML(expected, text)

        # add notes to beach
        beach.notes = "All of these words are part of the notes"
        beach.save()
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.b'})
        data = json.loads(result.content.decode('utf-8'))
        assert len(data['results']) == 1
        text = data['results'][0]['text']
        # first 5 words of notes field should be present in response
        # on a separate line
        expected = ('<strong>Sylvia Beach (1900 - 1970)</strong> '
                    'sylv.b <br />All of these words are')
        self.assertInHTML(expected, text)

        # give Ms. Sylvia a mep id
        ms_sylvia.mep_id = 'sylv.a'
        ms_sylvia.save()
        # check that mep.id shows up in result
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.a'})
        data = json.loads(result.content.decode('utf-8'))
        text = data['results'][0]['text']
        self.assertInHTML('<strong>Ms. Sylvia</strong> sylv.a', text)
        # give Ms. Sylvia events
        account = Account.objects.create()
        account.persons.add(ms_sylvia)
        Subscription.objects.create(
            account=account,
            start_date=date(1971, 1, 2),
            end_date=date(1971, 1, 31),
        )
        Subscription.objects.create(
            account=account,
            start_date=date(1971, 1, 1),
            end_date=date(1971, 1, 31),
        )
        # first event by start_date should be displayed
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.a'})
        data = json.loads(result.content.decode('utf-8'))
        text = data['results'][0]['text']
        print(text)
        expected = ('<strong>Ms. Sylvia</strong> sylv.a <br />'
                    'Subscription (1971-01-01 - 1971-01-31)')
        self.assertInHTML(expected, text)



    def test_person_admin_change(self):
        # create user with permission to load admin edit form
        su_password = 'itsasecret'
        superuser = User.objects.create_superuser(username='admin',
            password=su_password, email='su@example.com')

        # login as admin user
        self.client.login(username=superuser.username, password=su_password)

        # create two people and a relationship
        m_dufour = Person.objects.create(name='Charles Dufour')
        mlle_dufour = Person.objects.create(name='Dufour', title='Mlle')
        parent = RelationshipType.objects.create(name='parent')
        rel = Relationship.objects.create(from_person=mlle_dufour,
            relationship_type=parent, to_person=m_dufour, notes='relationship uncertain')
        person_edit_url = reverse('admin:people_person_change',
            args=[m_dufour.id])
        result = self.client.get(person_edit_url)
        self.assertContains(result, 'Relationships to this person')
        self.assertContains(result, str(mlle_dufour),
            msg_prefix='should include name of person related to this person ')
        self.assertContains(result, reverse('admin:people_person_change',
            args=[mlle_dufour.id]),
            msg_prefix='should include edit link for person related to this person')
        self.assertContains(result, parent.name,
            msg_prefix='should include relationship name')
        self.assertContains(result, rel.notes,
            msg_prefix='should include any relationship notes')

    def test_person_admin_list(self):
        # create user with permission to load admin edit form
        su_password = 'itsasecret'
        superuser = User.objects.create_superuser(username='admin',
            password=su_password, email='su@example.com')

        # login as admin user
        self.client.login(username=superuser.username, password=su_password)

        # create two people and a relationship
        Person.objects.create(name='Charles Dufour')
        Person.objects.create(name='Dufour', title='Mlle')

        # get the list url with logged in user
        person_list_url = reverse('admin:people_person_changelist')
        result = self.client.get(person_list_url)

        self.assertContains(result, Person.address_count.short_description,
            msg_prefix='should have address_count field and short_desc.')
        self.assertContains(result, Person.list_nationalities.short_description,
            msg_prefix='should have list_nationalities field and short desc.')


class TestGeonamesLookup(TestCase):

    def test_geonames_get_label(self):
        geo_lookup = GeoNamesLookup()
        item = {'name': 'New York City', 'countryName': 'USA'}
        # country code used if available
        assert geo_lookup.get_label(item) == 'New York City, USA'
        del item['countryName']
        # and just name, if no country is available
        assert geo_lookup.get_label(item) == 'New York City'


class TestGeonamesLookupWidget(TestCase):

    def test_render(self):
        widget = GeoNamesLookupWidget()
        # no value set - should not error
        rendered = widget.render('place', None, {'id': 'place'})
        assert '<p><a id="geonames_uri" target="_blank" href=""></a></p>' \
            in rendered
        # uri value set - should be included in generated link
        uri = 'http://sws.geonames.org/2759794/'
        rendered = widget.render('place', uri, {'id': 'place'})
        assert '<a id="geonames_uri" target="_blank" href="%(uri)s">%(uri)s</a>' \
            % {'uri': uri} in rendered
        # value should be set as an option to preserve existing
        # value when the form is submitted
        assert '<option value="%(uri)s" selected>%(uri)s</option' % \
            {'uri': uri} in rendered


class TestMapWidget(TestCase):

    def test_render(self):
        widget = MapWidget()
        # no value set - should not error
        rendered = widget.render('place', None, {'id': 'place'})
        assert '<div id="geonames_map"></div>' in rendered


class TestCountryAutocompleteView(TestCase):

    def test_get_queryset(self):
        # make two countries
        Country.objects.create(name='Spain', code='ES', geonames_id='001')
        Country.objects.create(name='France', code='FR', geonames_id='002')

        # send a request, test view and queryset indirectly
        auto_url = reverse('people:country-autocomplete')
        res = self.client.get(auto_url, {'q': 'Spa'})
        assert res
        info = res.json()
        assert info['results']
        assert info['results'][0]['text'] == 'Spain'

        res = self.client.get(auto_url, {'q': 'Fra'})
        assert res
        info = res.json()
        assert info['results']
        assert info['results'][0]['text'] == 'France'


class TestLocationAutocompleteView(TestCase):

    def test_get_queryset(self):
        # make two countries
        es = Country.objects.create(name='Spain', code='ES', geonames_id='001')
        fr = Country.objects.create(name='France', code='FR', geonames_id='002')

        # make two addresses
        add_dict = {
            'name': 'Hotel Le Foo',
            'street_address': 'Rue Le Bar',
            'city': 'Paris',
            'postal_code': '012345',
            'country': fr,
        }
        add_dict2 = {
            'name': 'Hotel El Foo',
            'street_address': 'Calle El Bar',
            'city': 'Madrid',
            'postal_code': '678910',
            'country': es,
        }
        add1 = Location.objects.create(**add_dict)
        Location.objects.create(**add_dict2)

        # make a person
        person = Person.objects.create(name='Baz', title='Mr.', sort_name='Baz')

        # - series of tests for get_queryset Q's and view rendering
        # autocomplete that should get both
        auto_url = reverse('people:location-autocomplete')
        res = self.client.get(auto_url, {'q': 'Foo'})
        info = res.json()
        assert len(info['results']) == 2

        # auto complete that should get Le Foo
        res = self.client.get(auto_url, {'q': 'Rue'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel Le Foo' in info['results'][0]['text']

        # auto complete that should get Le Foo
        res = self.client.get(auto_url, {'q': 'Fra'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel Le Foo' in info['results'][0]['text']


        # auto complete that should get El Foo
        res = self.client.get(auto_url, {'q': '67891'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel El Foo' in info['results'][0]['text']

        # auto complete that should get El Foo
        res = self.client.get(auto_url, {'q': 'Mad'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel El Foo' in info['results'][0]['text']

        # autocomplete that should also find location by associated person
        Address.objects.create(location=add1, person=person)
        res = self.client.get(auto_url, {'q': 'Baz'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel Le Foo' in info['results'][0]['text']
