from unittest.mock import patch
from django.test import TestCase, override_settings

import pytest
import requests

from mep.people.geonames import GeoNamesAPI, GeoNamesError, \
    GeoNamesUnauthorized


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
        mock_result = {'geonames': []}
        mockrequests.get.return_value.json.return_value = mock_result
        mockrequests.codes = requests.codes
        mockrequests.get.return_value.status_code = requests.codes.ok
        mockrequests.get.return_value.reason = 'OK'

        geo_api = GeoNamesAPI()

        result = geo_api.search('amsterdam')
        assert result == []
        mockrequests.get.assert_called_with('http://api.geonames.org/searchJSON',
            params={'username': 'test_geonames_user', 'q': 'amsterdam'})

        # with max specified
        result = geo_api.search('london', max_rows=20)
        mockrequests.get.assert_called_with('http://api.geonames.org/searchJSON',
            params={'username': 'test_geonames_user', 'q': 'london',
                    'maxRows': 20})

        # feature class
        geo_api.search('canada', feature_class='A')
        mockrequests.get.assert_called_with('http://api.geonames.org/searchJSON',
            params={'username': 'test_geonames_user', 'q': 'canada',
                    'featureClass': 'A'})
        # feature code
        geo_api.search('canada', feature_code='PCLI')
        mockrequests.get.assert_called_with('http://api.geonames.org/searchJSON',
            params={'username': 'test_geonames_user', 'q': 'canada',
                    'featureCode': 'PCLI'})

    def test_uri_from_id(self):
        assert GeoNamesAPI.uri_from_id(12345) == \
            'http://sws.geonames.org/12345/'

    @patch('mep.people.geonames.requests')
    def test_countries(self, mockrequests):
        mockrequests.get.return_value.json.return_value = self.mock_countryinfo
        mockrequests.codes = requests.codes
        mockrequests.get.return_value.status_code = requests.codes.ok
        mockrequests.get.return_value.reason = 'OK'

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
        mockrequests.get.return_value.reason = 'OK'

        geo_api = GeoNamesAPI()
        assert 'AD' in geo_api.countries_by_code
        assert geo_api.countries_by_code['AD']['countryName'] == 'Andorra'
        assert 'AE' in geo_api.countries_by_code
        assert geo_api.countries_by_code['AE']['geonameId'] == 290557

    @patch('mep.people.geonames.requests')
    def test_errors(self, mockrequests):
        mockrequests.codes = requests.codes
        mockrequests.get.return_value.status_code = requests.codes.ok
        mockrequests.get.return_value.reason = 'OK'

        # no result found
        error_message = {
            "status": {
              "message": "no administrative country subdivision for latitude and longitude :51.03,-20.0",
              "value": 15
            }
        }
        mockrequests.get.return_value.json.return_value = error_message
        geo_api = GeoNamesAPI()
        # generic error
        with pytest.raises(GeoNamesError) as geo_err:
            geo_api.call_api('testmethod')

        # exception text should include geonames api message
        assert error_message['status']['message'] in str(geo_err)

        # unauthorized error
        error_message = {
            "status": {
              "message": "invalid username or no username supplied",
              "value": 10
            }
        }
        mockrequests.get.return_value.json.return_value = error_message
        # unauthorized error
        with pytest.raises(GeoNamesUnauthorized) as geo_err:
            geo_api.call_api('testmethod')

        assert error_message['status']['message'] in str(geo_err)
