from unittest.mock import patch
from django.test import TestCase, override_settings

import requests

from mep.people.geonames import GeoNamesAPI


# test geonames api username for test (not an actual username)
GEONAMES_TEST_USER = 'test_geonames_user'


@override_settings(GEONAMES_USERNAME=GEONAMES_TEST_USER)
class TestGeonamesApi(TestCase):
    # minimal, simplified version of country data from geonames api
    mock_countryinfo = {
        'geonames': [{
            'continent': "EU",
            'geonameId': 3041565,
            'isoAlpha3': "AND",
            'fipsCode': "AN",
            'countryCode': "AD",
            'countryName': "Andorra",
        },
        {
            'continent': "AS",
            'geonameId': 290557,
            'isoAlpha3': "ARE",
            'fipsCode': "AE",
            'countryCode': "AE",
            'countryName': "United Arab Emirates",
            }
        ]
    }

    def test_init(self):
        geo_api = GeoNamesAPI()
        # username should be set from django config
        assert geo_api.username == 'test_geonames_user'

    @patch('mep.people.geonames.requests')
    def test_search(self, mockrequests):
        geo_api = GeoNamesAPI()

        mock_result = {'geonames': []}

        mockrequests.get.return_value.json.return_value = mock_result
        result = geo_api.search('amsterdam')
        assert result == []
        mockrequests.get.assert_called_with('http://api.geonames.org/searchJSON',
            params={'username': 'test_geonames_user', 'q': 'amsterdam'})

        # with max specified
        result = geo_api.search('london', max_rows=20)
        mockrequests.get.assert_called_with('http://api.geonames.org/searchJSON',
            params={'username': 'test_geonames_user', 'q': 'london',
                    'maxRows': 20})

    def test_uri_from_id(self):
        assert GeoNamesAPI.uri_from_id(12345) == \
            'http://sws.geonames.org/12345/'

    @patch('mep.people.geonames.requests')
    def test_countries(self, mockrequests):
        mockrequests.get.return_value.json.return_value = self.mock_countryinfo
        mockrequests.codes = requests.codes
        mockrequests.get.return_value.status_code = requests.codes.ok

        geo_api = GeoNamesAPI()

        assert geo_api.countries == self.mock_countryinfo['geonames']
        mockrequests.get.assert_called_with('http://api.geonames.org/countryInfoJSON',
                                            params={'username': GEONAMES_TEST_USER})

        # result should be cached and api not called second time
        mockrequests.reset_mock()
        geo_api.countries
        mockrequests.get.assert_not_called()

    @patch('mep.people.geonames.requests')
    def test_countries_by_code(self, mockrequests):
        mockrequests.get.return_value.json.return_value = self.mock_countryinfo
        mockrequests.codes = requests.codes
        mockrequests.get.return_value.status_code = requests.codes.ok

        geo_api = GeoNamesAPI()
        assert 'AD' in geo_api.countries_by_code
        assert geo_api.countries_by_code['AD']['countryName'] == 'Andorra'
        assert 'AE' in geo_api.countries_by_code
        assert geo_api.countries_by_code['AE']['geonameId'] == 290557

