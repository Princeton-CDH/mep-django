import datetime
import logging

from django.db import models
from django.urls import reverse
from parasolr.indexing import Indexable
import rdflib
import requests

from mep.common.models import Named, Notable
from mep.common.validators import verify_latlon
from mep.books.oclc import WorldCatEntity
from mep.people.models import Person


logger = logging.getLogger(__name__)


class PublisherPlace(Named, Notable):
    '''Model for place where publishers are located'''
    # NOTE: Using decimal field here to set precision on the head
    # FloatField uses float, which can introduce unexpected rounding.
    # This would let us have measurements down to the tree level, if necessary

    # QUESTION: Do we want to add a Geonames ID for this?
    latitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        validators=[verify_latlon]
    )
    longitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        validators=[verify_latlon]
    )


class Publisher(Named, Notable):
    '''Model for publishers'''


class Format(Named, Notable):
    '''Format of items in the library (book, periodical, etc)'''
    #: linked data URI for the format
    uri = models.URLField("URI", help_text="Format or type URI", unique=True)


class Subject(models.Model):
    '''Linked data subjects for describing :class:`Item`'''

    #: name/label for the subject (required but not required unique)
    name = models.CharField(max_length=255)
    #: linked data URI for the subject
    uri = models.URLField("URI", help_text="Subject URI", unique=True)
    #: rdf type for the subject
    rdf_type = models.URLField("RDF Type")

    def __str__(self):
        return '%s (%s)' % (self.name, self.uri)

    def __repr__(self):
        return '<Subject %s (%s)>' % (self.uri, self.name)

    @classmethod
    def create_from_uri(cls, uri):
        '''Initialize a new :class:`Subject` from a URI. Loads the URI
        as an :class:`rdflib.Graph` in order to pull the preferred label
        and RDF type for the URI.'''

        # as for OCLC code, using requests to load RDF content
        # for more fine-grained control and fewer errors for batch work,
        # and current SSL support (i.e. for VIAF)
        graph = rdflib.Graph()
        request_uri = uri
        uriref = rdflib.URIRef(uri)
        # worldcat FAST URIs don't support content negotation,
        # so explicitly request RDF content based on known URL format
        request_headers = {}
        if uri.startswith('http://id.worldcat.org/fast/'):
            request_uri = '%s.rdf.xml' % request_uri.rstrip('/')
        elif uri.startswith('http://id.loc.gov/authorities/'):
            # at least one LOC url is redirecting alternately
            # to an HTML version and json-ld, so explicitly request json-ld
            request_uri = '%s.jsonld' % request_uri
        else:
            request_headers = {'accept': 'application/rdf+xml'}
        response = requests.get(request_uri, headers=request_headers)

        # exclude html responses, since they can't be parsed
        # (some LOC json requests are redirecting to html)
        # Possibly useful? LoC responses include a X-PrefLabel header,
        # could just use that (and make type optional)
        if response.status_code == requests.codes.ok and \
          not response.headers['content-type'].startswith('text/html'):
            parse_opts = {}
            # some results return json-ld, and rdflib does not autodetect
            if response.headers['content-type'] == 'application/ld+json':
                parse_opts['format'] = 'json-ld'

            graph.parse(data=response.content.decode(), **parse_opts)

            label_opts = {}
            # viaf records include multiple languages and some records
            # have language codes for them; try with language filter first
            if 'viaf.org' in uri:
                label_opts['lang'] = 'en-US'
            labels = graph.preferredLabel(uriref, **label_opts)
            # if no labels were found with language tag, try without
            if not labels:
                labels = graph.preferredLabel(uriref)
            # if still no labels, bail out
            if not labels:
                return
            # preferred label returns a list of predicate, object
            # use the object for the first result
            name = str(labels[0][1])
            rdf_type = str(graph.value(uriref, rdflib.RDF.type))
            return Subject.objects.create(uri=uri, name=name,
                                          rdf_type=rdf_type)

        # if the request failed or was not usable, log the error
        logger.warning('Error creating Subject for %s (response %s)',
                       uri, response.status_code)


class Item(Notable, Indexable):
    '''Primary model for :mod:`books` module, also used for journals,
    and other media types.'''
    #: mep id from stub records imported from xml
    mep_id = models.CharField(
        max_length=255, blank=True, unique=True,
        verbose_name='MEP ID', null=True)
    # NOTE: mep_id has null=true so we can enforce unique constraint but
    # allow for items with no mep id

    title = models.CharField(max_length=255, blank=True)
    volume = models.PositiveSmallIntegerField(blank=True, null=True)
    number = models.PositiveSmallIntegerField(blank=True, null=True)
    year = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name='Date of Publication')
    season = models.CharField(max_length=255, blank=True)
    edition = models.CharField(max_length=255, blank=True)
    uri = models.URLField(blank=True, verbose_name='Work URI',
                          help_text="Linked data URI for this work")
    edition_uri = models.URLField(
        blank=True, verbose_name='Edition URI',
        help_text="Linked data URI for this edition, if known")
    genre = models.CharField(
        max_length=255, blank=True, help_text='Genre from OCLC Work record')
    item_format = models.ForeignKey(
        Format, verbose_name='Format', null=True, blank=True,
        help_text='Format of the item, e.g. book or periodical')

    #: update timestamp
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # QUESTION: On the diagram these are labeled as FK, but they seem to imply
    # M2M (i.e. more than one publisher or more than one pub place?)
    publishers = models.ManyToManyField(Publisher, blank=True)
    pub_places = models.ManyToManyField(
        PublisherPlace, blank=True, verbose_name="Places of Publication")

    # direct access to all creator persons, using Creator as through model
    creators = models.ManyToManyField(Person, through='Creator')

    #: optional subjects, from OCLC work record
    subjects = models.ManyToManyField(Subject, blank=True)

    def save(self, *args, **kwargs):
        # override save to ensure mep ID is None rather than empty string
        # if not set
        if not self.mep_id:
            self.mep_id = None
        super(Item, self).save(*args, **kwargs)

    def __repr__(self):
        return '<Item %s>' % self.__dict__

    def __str__(self):
        year_str = ''
        if self.year:
            year_str = '(%s)' % self.year
        str_value = ('%s %s' % (self.title, year_str)).strip()
        if str_value:
            return str_value
        return '(No title, year)'

    def creator_by_type(self, creator_type):
        '''return item creators of a single type, e.g. author'''
        return self.creators.filter(creator__creator_type__name=creator_type)

    @property
    def authors(self):
        '''item creators with type author'''
        return self.creator_by_type('Author')

    def author_list(self):
        '''semicolon separated list of author names'''
        return '; '.join([str(auth) for auth in self.authors])
    author_list.verbose_name = 'Authors'

    @property
    def editors(self):
        '''item creators with type editor'''
        return self.creator_by_type('Editor')

    @property
    def translators(self):
        '''item creators with type translator'''
        return self.creator_by_type('Translator')

    @property
    def borrow_count(self):
        '''Number of times this item was borrowed.'''
        return self.event_set.filter(borrow__isnull=False).count()

    def admin_url(self):
        '''URL to edit this record in the admin site'''
        return reverse('admin:books_item_change', args=[self.id])
    admin_url.verbose_name = 'Admin Link'

    def has_uri(self):
        '''Is the URI is set for this item?'''
        return self.uri != ''
    has_uri.boolean = True

    def subject_list(self):
        '''semicolon separated list of subject names'''
        return '; '.join([subj.name for subj in self.subjects.all()])

    def format(self):
        '''format of this item if known (e.g. book or periodical)'''
        return self.item_format.name if self.item_format else ''

    def index_data(self):
        '''data for indexing in Solr'''

        index_data = super().index_data()

        index_data.update({
            'title_s': self.title,
            # include pk for now for item detail url
            'pk_i': self.pk,
            'authors_t': [str(a) for a in self.authors] if self.authors else None,
            'editors_t': [str(e) for e in self.editors] if self.editors else None,
            'translators_t': [str(t) for t in self.translators] if self.translators else None,
            'pub_date_i': self.year,
        })

        return index_data

    @property
    def first_known_interaction(self):
        '''date of the earliest known interaction for this item'''

        # search for the earliest start date, excluding any borrow
        # or purchase events with unknown years
        first_event = self.event_set \
            .filter(start_date__isnull=False) \
            .exclude(borrow__start_date_precision__knownyear=False) \
            .exclude(purchase__start_date_precision__knownyear=False) \
            .order_by('start_date').first()

        if first_event:
            return first_event.start_date

    def populate_from_worldcat(self, worldcat_entity):
        '''Set work URI, edition URI, genre, item type, and subjects
        based on a WorldCat record.'''

        # work URI apparently not available in all cases; set to
        # empty string instead of None/null
        self.uri = worldcat_entity.work_uri or ''
        self.edition_uri = worldcat_entity.item_uri
        self.genre = worldcat_entity.genre or ''
        # types will be prepopulated to work with OCLC search results
        # (predominantly books and periodicals), but in future
        # we may need a method to create format from uri as for subjects
        if worldcat_entity.item_type:
            self.item_format = Format.objects.get(uri=worldcat_entity.item_type)

        subject_uris = worldcat_entity.subjects
        if subject_uris:
            # find existing subjects already in the database
            subjects = list(Subject.objects.filter(uri__in=subject_uris))
            # create any new subjects that don't already exist
            new_subject_uris = set(subject_uris) - \
                               set(subj.uri for subj in subjects)
            for subject_uri in new_subject_uris:
                # try to create the subject
                subject = Subject.create_from_uri(subject_uri)
                # if successful, add to the list
                if subject:
                    subjects.append(subject)
            # set subjects on this item (replacing any previously set)
            self.subjects.set(subjects)


class CreatorType(Named, Notable):
    '''Type of creator role a person can have to an item; author,
    editor, translator, etc.'''


class Creator(Notable):
    creator_type = models.ForeignKey(CreatorType)
    person = models.ForeignKey(Person)
    item = models.ForeignKey(Item)

    def __str__(self):
        return '%s %s %s' % (self.person, self.creator_type, self.item)
