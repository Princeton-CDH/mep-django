import logging

from cached_property import cached_property
from django.conf import settings
import requests


logger = logging.getLogger(__name__)


# NOTE: geonames code copied/adapted from winthrop project; will need
# to be spun off into its own library at some point down ther oad

class GeoNamesAPI(object):
    '''Minimal wrapper around GeoNames API.  Currently supports simple
    searching by name and generating a uri from an id.  Expects
    **GEONAMES_USERNAME** to be configured in django settings.'''

    api_base = 'http://api.geonames.org'

    # store country info on the *class* so it can be fetched once and shared
    _countries = None

    def __init__(self):
        self.username = getattr(settings, "GEONAMES_USERNAME", None)

    def search(self, query, max_rows=None, feature_class=None,
        feature_code=None):
        '''Search for places and return the list of results'''
        api_url = '%s/%s' % (self.api_base, 'searchJSON')
        # NOTE: for autocomplete, name_startsWith might be better
        params = {'username': self.username, 'q': query}
        if max_rows is not None:
            params['maxRows'] = max_rows
        if feature_class is not None:
            params['featureClass'] = feature_class
        if feature_code is not None:
            params['featureCode'] = feature_code
        response = requests.get(api_url, params=params)
        logger.debug('GeoNames search \'%s\': %s %s, %0.2f sec',
                     query, response.status_code, response.reason,
                     response.elapsed.total_seconds())
        # return the list of results (present even when empty)
        return response.json()['geonames']

    @classmethod
    def uri_from_id(cls, geonames_id):
        '''Convert a GeoNames id into a GeoNames URI'''
        return 'http://sws.geonames.org/%d/' % geonames_id

    @property
    def countries(self):
        '''Country information as returned by countryInfoJSON.'''
        if GeoNamesAPI._countries is None:
            api_url = '%s/%s' % (self.api_base, 'countryInfoJSON')
            response = requests.get(api_url, params={'username': self.username})
            logger.debug('GeoNames countryInfoJSON: %s %s, %0.2f sec',
                         response.status_code, response.reason,
                         response.elapsed.total_seconds())
            if response.status_code == requests.codes.ok:
                GeoNamesAPI._countries = response.json().get('geonames', [])

        return GeoNamesAPI._countries

    @cached_property
    def countries_by_code(self):
        return {country['countryCode']: country for country in self.countries}
