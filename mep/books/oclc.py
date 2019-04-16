'''
Module for collecting OCLC search functionality, particularly SRU style
searches.
'''
from io import BytesIO, StringIO
from logging import getLogger
import time

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
        # should we set a contact header?
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
        start = time.time()
        try:
            response = self.session.get(
                ('%s/%s' % (self.WORLDCAT_API_BASE,
                            self.API_ENDPOINT)).strip('/'),
                params=kwargs)
            # log the url call and response time
            logger.debug('search %s => %d: %f sec',
                         self.query_string, response.status_code,
                         time.time() - start)
            if response.status_code == requests.codes.ok:
                return response
        except requests.exceptions.ConnectionError as err:
            logger.exception(err)


class SRWResponse(xmlmap.XmlObject):
    '''Object to parse SRW formatted responses.'''
    ROOT_NAMESPACES = {
        'srw': 'http://www.loc.gov/zing/srw/'
    }

    #: number of records found for the query
    num_records = xmlmap.IntegerField('srw:numberOfRecords')
    #: returned records as :class:`~eulxml.xmlmap.XmlObject`
    records = xmlmap.NodeField('srw:records', xmlmap.XmlObject)

    @property
    def marc_records(self):
        # serialize xml to a bytebytestream for loading by pymarc
        bytestream = BytesIO()
        self.serializeDocument(bytestream)
        bytestream.seek(0)
        # pymarc is returning 'None' in the array alternating with
        # pymarc records; not sure why, but filter them out
        return list(filter(None, pymarc.parse_xml_to_array(bytestream)))


class SRUSearch(WorldCatClientBase):
    '''Client for peforming an SRU (specific edition) based search'''

    API_ENDPOINT = 'search/worldcat/sru'

    def __init__(self):
        super().__init__()

    # mapping of field lookup to srw field abbreviation
    search_fields = {
        'title': 'ti',
        'author': 'au',
        'year': 'yr',
        'keyword': 'kw'
    }

    def filter(self, *args, **kwargs):
        '''Add another filter to the :class:`SRUSearch` object and return
        self to allow chaining.'''
        search_copy = self._clone()
        search_copy.query.extend(args)
        for key, val in kwargs.items():
            # split field on __ to allow for specifying operator
            field_parts = key.split('__', 1)
            field = field_parts[0]

            # convert readable field names to srw field via lookup
            if field in self.search_fields:
                field = 'srw.%s' % self.search_fields[field]

            if len(field_parts) > 1:
                # spaces needed for everything besides = (?)
                operator = ' %s ' % field_parts[1]
            else:
                # assume equal if not specified
                operator = '='

            # *maybe* could infer when to wrap quotes around val
            # based on type (e.g. str vs numeric)

            search_copy.query.append('%s%s%s' % (field, operator, val))

        return search_copy

    def _clone(self):
        search_copy = self.__class__()
        search_copy.query = list(self.query)
        return search_copy

    def search(self, **kwargs):
        '''Perform a CQL based search based on chained filters.'''
        response = super().search(**kwargs)
        if response:
            # parse and return as SRW Response
            return xmlmap.load_xmlobject_from_string(
                response.content, SRWResponse)
