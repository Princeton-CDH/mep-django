'''
Module for collecting OCLC search functionality, particularly SRU style
searches.
'''
from io import BytesIO
import logging
import time
from typing import List, Dict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from eulxml import xmlmap
from lxml.etree import XMLSyntaxError
import pymarc
import rdflib
import requests

from mep import __version__ as mep_version


logger = logging.getLogger(__name__)


class WorldCatClientBase:
    '''Mixin base for clients interacting with the Worldcat API.'''

    WORLDCAT_API_BASE = 'http://www.worldcat.org/webservices/catalog'
    API_ENDPOINT = ''

    def __init__(self):

        # Get WSKey or error if not specified
        self.wskey = getattr(settings, 'OCLC_WSKEY', None)
        if not self.wskey:
            raise ImproperlyConfigured('OCLC search functionality '
                                       'requires a WSKEY.')
        # Configure a session to use WS_KEY
        self.session = requests.Session()
        headers = {
            'User-Agent': 'mep-django/%s (python-requests/%s)' % \
                (mep_version, requests.__version__)
        }
        # include technical contact as From header, if set
        tech_contact = getattr(settings, 'TECHNICAL_CONTACT', None)
        if tech_contact:
            headers['From'] = tech_contact
        self.session.headers.update(headers)

    def search(self, *args, **kwargs):
        '''Extendable method to process the results of a search query'''
        params = kwargs.copy()
        # wskey required for search
        params['wskey'] = self.wskey

        start = time.time()
        try:
            response = self.session.get(
                ('%s/%s' % (self.WORLDCAT_API_BASE,
                            self.API_ENDPOINT)).strip('/'),
                params=params)
            # log the url call and response time
            # assuming there is always a query arg for now...
            logger.debug('search %s => %d: %f sec',
                         kwargs['query'], response.status_code,
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
    def marc_records(self) -> List[pymarc.record.Record]:
        '''List of MARC records included in the response'''
        # serialize xml to a bytebytestream for loading by pymarc
        bytestream = BytesIO()
        self.serializeDocument(bytestream)
        bytestream.seek(0)
        # pymarc is returning 'None' in the array alternating with
        # pymarc records; not sure why, but filter them out
        return list(filter(None, pymarc.parse_xml_to_array(bytestream)))


def oclc_uri(marc_record: pymarc.record.Record) -> str:
    """Generate the worldcat URI for an OCLC MARC record"""
    return 'http://www.worldcat.org/oclc/%s' % marc_record['001'].value()


#: schema.org RDF namespace
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')


class SRUSearch(WorldCatClientBase):
    '''Client for peforming an SRU (specific edition) based search'''

    API_ENDPOINT = 'search/worldcat/sru'

    #: mapping of field lookup to srw field abbreviation
    search_fields = {
        'title': 'ti',
        'author': 'au',
        'year': 'yr',
        'keyword': 'kw'
    }

    @staticmethod
    def _lookup_to_search(*args: List[str], **kwargs: Dict) -> str:
        '''Take a list of search terms and dictionary of field lookups
        and return as as a CQL search string. List arguments are included
        in the query as-is. Dictionary lookup supports field names in
        :attr:`SRUSearch.search_fields` and supports `__` for operators
        such as any, or all (e.g. title__all or author__any). If no
        operator is specified, will use equals.
        '''
        search_query = []

        # any args are added to the search query as-is
        search_query.extend(args)

        for key, value in kwargs.items():
            # split field on __ to allow for specifying operator
            field_parts = key.split('__', 1)
            field = field_parts[0]

            # convert readable field names to srw field via lookup
            if field in SRUSearch.search_fields:
                field = 'srw.%s' % SRUSearch.search_fields[field]

            # determine operator to use
            if len(field_parts) > 1:  # operator specified via __
                # spaces needed for everything besides = (?)
                operator = ' %s ' % field_parts[1]
            else:
                # assume equal if not specified
                operator = '='

            # if value is a string, wrap in quotes
            if isinstance(value, str):
                value = '"%s"' % value
            search_query.append('%s%s%s' % (field, operator, value))

        return ' AND '.join(search_query)

    def search(self, *args, **kwargs):
        '''Perform a CQL based search based on chained filters.'''
        search_query = SRUSearch._lookup_to_search(*args, **kwargs)
        response = super().search(query=search_query)
        if response:
            # parse and return as SRW Response
            try:
                return xmlmap.load_xmlobject_from_string(
                    response.content, SRWResponse)
            except XMLSyntaxError as err:
                # occasionally getting parsing error exceptions; log it
                # include first part of response content in case it helps
                logger.error('Error parsing response %s\n%s',
                             err, response.content[:100])
                # ... not sure what details are useful here

    def get_work_uri(self, marc_record: pymarc.record.Record) -> str:
        """Given a MARC record from OCLC, find and return the work URI"""

        # NOTE: doesn't technically be part of SRUSearch;
        # primarily here to allow sharing the requests session

        graph = rdflib.Graph()
        # control field in 001 is OCLC identifier, used for URIs
        item_uri = oclc_uri(marc_record)
        # let rdflib handle content-type negotiation and parsing
        # - URI + extension should return requested type
        response = self.session.get("%s.rdf" % item_uri)
        if response.status_code == requests.codes.ok:
            graph.parse(data=response.content.decode())

            # get the URI for schema:exampleOfWork and return as a string
            return str(graph.value(subject=rdflib.URIRef(item_uri),
                                   predicate=SCHEMA_ORG.exampleOfWork))

        # log an error for any other status
        logger.error('Error loading OCLC record as RDF %s => %d',
                     item_uri, response.status_code)
