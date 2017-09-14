import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.test import TestCase
from django.urls import reverse

from mep.people.admin import GeoNamesLookupWidget, MapWidget
from mep.people.geonames import GeoNamesAPI
from mep.people.models import Person, Relationship, RelationshipType
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
        Person.objects.create(name='Sylvia Beach')

        pub_autocomplete_url = reverse('people:autocomplete')
        result = self.client.get(pub_autocomplete_url, {'q': 'beach'})
        assert result.status_code == 200
        # decode response to inspect
        data = json.loads(result.content.decode('utf-8'))
        assert data['results'][0]['text'] == 'Sylvia Beach'

        # no match - shouldn't error
        result = self.client.get(pub_autocomplete_url, {'q': 'beauvoir'})
        assert result.status_code == 200
        data = json.loads(result.content.decode('utf-8'))
        assert not data['results']

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
