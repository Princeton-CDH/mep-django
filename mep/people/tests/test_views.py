import json
from unittest.mock import patch

from django.http import JsonResponse
from django.test import TestCase
from django.urls import reverse

from mep.people.admin import GeoNamesLookupWidget, MapWidget
from mep.people.geonames import GeoNamesAPI
from mep.people.models import Person
from mep.people.views import GeoNamesLookup


class TestPeopleViews(TestCase):

    @patch('mep.people.views.GeoNamesAPI')
    def test_geonames_autocomplete(self, mockgeonamesapi):
        geo_lookup_url = reverse('people:geonames-lookup')
        result = self.client.get(geo_lookup_url,
            params={'q': 'amsterdam'})
        # abbreviated sample return with fields currently in use
        mock_response = [
            {'name': 'New York City', 'geonameId': 5128581,
             'countryName': 'USA', 'lat': 40.71427, 'lng': -74.00597,
             'countryCode': 'US'}
        ]
        mockgeonamesapi.return_value.search.return_value = mock_response
        # patch in real uri from id logic
        mockgeonamesapi.return_value.uri_from_id = GeoNamesAPI.uri_from_id

        result = self.client.get(geo_lookup_url,
            params={'q': 'new york'})
        assert isinstance(result, JsonResponse)
        assert result.status_code == 200
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


class TestMapWidget(TestCase):

    def test_render(self):
        widget = MapWidget()
        # no value set - should not error
        rendered = widget.render('place', None, {'id': 'place'})
        assert '<div id="geonames_map"></div>' in rendered
