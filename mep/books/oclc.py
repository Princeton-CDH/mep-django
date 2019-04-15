'''
Module for collecting OCLC search functionality, particularly SRU style
searches.
'''
from io import BytesIO
from logging import getLogger

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from eulxml import xmlmap
import pymarc
import requests

logger = getLogger(__name__)


class WorldCatClientBase:
    '''Mixin base for clients interacting with the Worldcat API.'''

    WORLDCAT_API_BASE = 'http://www.worldcat.org/webservices/catalog'
    API_ENDPOINT = ''

    def __init__(self):

        # Get WSKey or error if not specified
        wskey = getattr(settings, 'OCLC_WSKEY', None)
        if not wskey:
            raise ImproperlyConfigured('OCLC search functionality '
                                       'requires a WSKEY.')
        # Configure a session to use WS_KEY
        self.session = requests.Session()
        self.session.params.update({
            'wskey': wskey
        })
        # initialize an empty query
        self.query = []

    @property
    def query_string(self):
        """Return an AND formatting query string."""
        return ' AND '.join(self.query)


    def search(self, **kwargs):
        '''Extendable method to process the results of a search query'''
        kwargs.update({'query': self.query_string})
        try:
            response = self.session.get(
                ('%s/%s' % (self.WORLDCAT_API_BASE,
                            self.API_ENDPOINT)).strip('/'),
                params=kwargs)
            if response.status_code == requests.codes.OK:
                print('foo')
                return response
        except requests.RequestException as err:
            logger.exception(err)


class SrwResponse(xmlmap.XmlObject):
    '''Object to parse SRW formatted responses.'''
    ROOT_NAMESPACES = {
        'srw': 'http://www.loc.gov/zing/srw/'
    }

    num_records = xmlmap.IntegerField('srw:numberOfRecords')


class SruSearch(WorldCatClientBase):
    '''Client for peforming an SRU (specific edition) based search'''

    API_ENDPOINT = 'search/worldcat/sru'

    def __init__(self):
        super().__init__()
        self.num_records = 0

    def filter(self, filter_string):
        '''Add another filter to the :class:`SRUSearch` object and return
        self to allow chaining.'''
        self.query.append(filter_string)
        return self

    def search(self, **kwargs):
        '''Perform a CQL based search based on chained filters.'''
        response = super().search(**kwargs)
        if response:
            # set the number of records for use in pulling max count
            srw_response = xmlmap\
                .load_xmlobject_from_string(response.text, SrwResponse)
            if srw_response.is_valid():
                self.num_records = srw_response.num_records
        return pymarc.parse_xml_to_array(BytesIO(response.content))

