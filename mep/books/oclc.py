'''
Module for collecting OCLC search functionality, particularly SRU style
searches.
'''
from io import BytesIO
import logging
import time

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
    def marc_records(self):
        '''List of MARC records included in the response'''
        # serialize xml to a bytebytestream for loading by pymarc
        bytestream = BytesIO()
        self.serializeDocument(bytestream)
        bytestream.seek(0)
        # pymarc is returning 'None' in the array alternating with
        # pymarc records; not sure why, but filter them out
        return list(filter(None, pymarc.parse_xml_to_array(bytestream)))


#: schema.org RDF namespace
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')


class RdfResource(rdflib.resource.Resource):
    # Extend rdflib resource to fix string method. This is based
    # on their code, but actually works in python 3

    def __str__(self):
        return str(self._identifier)


class WorldCatEntity:
    '''Entity for a single WorldCat record, with support for
    loading linked data and accessing values.'''

    rdf_resource = None

    @staticmethod
    def oclc_uri(marc_record: pymarc.record.Record) -> str:
        """Generate the worldcat URI for an OCLC MARC record"""
        return 'http://www.worldcat.org/oclc/%s' % marc_record['001'].value()

    def __init__(self, marc_record: pymarc.record.Record, session: requests.Session):
        self.marc_record = marc_record
        self.session = session
        self.item_uri = WorldCatEntity.oclc_uri(self.marc_record)
        graph = self.get_oclc_rdf()
        # if loading the graph fails, raise an exception because
        # this object is unusable without it
        if not graph:
            raise ConnectionError('Failed to load RDF for %s' % self.item_uri)

        # initialize an rdflib.resource
        self.rdf_resource = RdfResource(graph, rdflib.URIRef(self.item_uri))

    def __str__(self):
        return self.item_uri

    def __repr__(self):
        return '<WorldCatEntity %s>' % self.item_uri

    def get_oclc_rdf(self) -> rdflib.Graph:
        '''Load the RDF for the OCLC URI for the MARC record for this
        entity.'''

        graph = rdflib.Graph()
        # control field in 001 is OCLC identifier, used for URIs
        response = self.session.get("%s.rdf" % self.item_uri)
        if response.status_code == requests.codes.ok:
            graph.parse(data=response.content.decode())
            return graph

        # log an error for any other status
        logger.error('Error loading OCLC record as RDF %s => %d',
                     self.item_uri, response.status_code)

    @property
    def work_uri(self):
        '''OCLC Work URI for this item'''
        value = self.rdf_resource.value(SCHEMA_ORG.exampleOfWork)
        return str(value) if value else None

    basic_item_types = set([str(SCHEMA_ORG.Book), str(SCHEMA_ORG.Periodical)])

    @property
    def item_type(self):
        '''item type URI (e.g. book or periodical), from rdf:type.
        Skips schema.org/CreativeWork if present in preference of
        a more specific type'''

        # handle some cases where we're getting an ebook or other version,
        # which could be a media object or microform as well as a book;
        # we only care about the book type

        # get a list of all rdf types for this resource, omitting the generic
        # schema.org creative work type
        # (URIRef comparison is unreliable, using strings instead)
        rdf_types = list(
            str(rdf_type) for rdf_type in self.rdf_resource.objects(rdflib.RDF.type)
            if str(rdf_type) != str(SCHEMA_ORG.CreativeWork))

        # if there's a book or periodical in the list, use that
        basic_type = set(rdf_types) & self.basic_item_types
        if basic_type:
            return basic_type.pop()
        # otherwise, use the first non-creative work rdf type
        if rdf_types:
            return rdf_types[0]

    @property
    def genres(self):
        '''List of item genres from schema.org/genre, if any'''
        return [str(genre)
                for genre in self.rdf_resource.objects(SCHEMA_ORG.genre)]

    @property
    def subjects(self):
        '''URIs that this item is about, from schema.org/about; omits
        experimental worldcat URIs, dewey.info URIs .'''
        # dewey.info URL not resolving...
        return [str(subject) for subject in self.rdf_resource.objects(SCHEMA_ORG.about)
                if 'experiment.worldcat.org' not in str(subject) and
                'dewey.info' not in str(subject)]


class SRUSearch(WorldCatClientBase):
    '''Client for peforming an SRU (specific edition) based search'''

    # See https://www.oclc.org/developer/develop/web-services/worldcat-search-api/bibliographic-resource.en.html
    # for specifics on available search fields

    API_ENDPOINT = 'search/worldcat/sru'

    #: mapping of field lookup to srw field abbreviation
    search_fields = {
        'title': 'ti',
        'author': 'au',
        'year': 'yr',
        'keyword': 'kw',
        'material_type': 'mt',
        'language_code': 'la'
    }

    @staticmethod
    def _lookup_to_search(*args, **kwargs):
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
            boolean_combination = ''

            # split field on __ to allow for specifying operator
            field_parts = key.split('__', 1)
            field = field_parts[0]

            # convert readable field names to srw field via lookup
            if field in SRUSearch.search_fields:
                field = 'srw.%s' % SRUSearch.search_fields[field]

            # determine operator to use
            if len(field_parts) > 1:  # operator specified via __

                # use leading "not" on operator as indicator to
                # use NOT instead of AND
                if field_parts[1].startswith('not'):
                    boolean_combination = 'NOT '
                    field_parts[1] = field_parts[1][3:]

                # spaces needed for everything besides =
                operator = ' %s ' % field_parts[1]
            else:
                # assume equal if not specified
                operator = '='

            # if value is a string, wrap in quotes
            if isinstance(value, str):
                value = '"%s"' % value
            search_query.append('%s%s%s%s' % \
                    (boolean_combination, field, operator, value))

        return ' AND '.join(search_query).replace(' AND NOT ', ' NOT ')

    def search(self, *args, **kwargs):
        '''Perform a CQL search generated from keyword arguments in a style
        similar to django querysets, e.g.::

            search(title__exact="Huckleberry Finn", year=1884,
                   material_type__notexact="Internet Resource")

        Supports the following fields:

            * title
            * author
            * year
            * keyword
            * material_type
            * language_code

        And the following operators:

            * exact, notexact

        'keyword': 'kw',
        'material_type': 'mt',
        'language_code': 'la'

        '''
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

    def get_worldcat_rdf(self, marc_record):
        '''Given a MARC record from OCLC, load the RDF for the corresponding
        OCLC URI'''

        # NOTE: doesn't technically need to be part of SRUSearch;
        # initialize here to allow sharing the requests session
        return WorldCatEntity(marc_record, self.session)
