import logging

from cached_property import cached_property
from django.conf import settings
import requests


logger = logging.getLogger(__name__)

# NOTE: geonames code adapted and extended from winthrop project; will need
# to be spun off into its own library at some point down ther oad


class GeoNamesError(Exception):
    '''Generic GeoNames response error'''


class GeoNamesUnauthorized(GeoNamesError):
    '''GeoNames unauthorized response (raised when username is not set)'''


class GeoNamesAPI(object):
    '''Minimal wrapper around GeoNames API.  Currently supports simple
    searching by name and generating a uri from an id.  Expects
    **GEONAMES_USERNAME** to be configured in django settings.'''

    api_base = 'http://api.geonames.org'

    # store country info on the *class* so it can be fetched once and shared
    _countries = None

    def __init__(self):
        self.username = getattr(settings, "GEONAMES_USERNAME", None)

    def call_api(self, method, params=None):
        # generic method to handle calling geonames api and raising
        # an exception if an error occurred
        api_url = '/'.join([self.api_base, method])
        if params is None:
            params = {}
        params['username'] = self.username
        response = requests.get(api_url, params=params)
        logger.debug('GeoNames %s: %s %s, %0.2f sec',
                     method, response.status_code, response.reason,
                     response.elapsed.total_seconds())
        if response.status_code == requests.codes.ok:
            # Unfortunately geonames api returns 200 codes for what
            # should be errors, with message and status code in the response.
            # See exception documentation for list of codes
            # http://www.geonames.org/export/webservice-exception.html
            data = response.json()
            if 'status' in data:
                if data['status']['value'] == 10:
                    raise GeoNamesUnauthorized(data['status']['message'])
                else:
                    raise GeoNamesError(data['status']['message'])

            return data

    def search(self, query, max_rows=None, feature_class=None,
        feature_code=None, name_start=False):
        '''Search for places and return the list of results'''
        api_method = 'searchJSON'

        params = {'username': self.username}
        # optionally use name start filter (e.g. for autocomplete)
        if name_start:
            params['name_startsWith'] = query
        # otherwise, generic search term query
        else:
            params['q'] = query

        if max_rows is not None:
            params['maxRows'] = max_rows
        if feature_class is not None:
            params['featureClass'] = feature_class
        if feature_code is not None:
            params['featureCode'] = feature_code

        return self.call_api(api_method, params)['geonames']

    @classmethod
    def uri_from_id(cls, geonames_id):
        '''Convert a GeoNames id into a GeoNames URI'''
        return 'http://sws.geonames.org/%d/' % geonames_id

    @property
    def countries(self):
        '''Country information as returned by countryInfoJSON.'''
        if GeoNamesAPI._countries is None:
            api_method = 'countryInfoJSON'
            GeoNamesAPI._countries = self.call_api(api_method)['geonames']

        return GeoNamesAPI._countries

    @cached_property
    def countries_by_code(self):
        '''Dictionary of country information keyed on two-letter code.'''
        return {country['countryCode']: country for country in self.countries}

    # def country_code(self):
    # http://api.geonames.org/countryCode?lat=47.03&lng=10.2&username=demo&type=json