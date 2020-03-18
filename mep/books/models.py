import logging

import rdflib
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils.html import format_html, strip_tags
from parasolr.django.indexing import ModelIndexable

from mep.accounts.partial_date import (DatePrecisionField, PartialDate,
                                       PartialDateMixin)
from mep.common.models import Named, Notable
from mep.common.validators import verify_latlon
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


class Genre(Named):
    '''Genres of items from OCLC'''


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


class WorkSignalHandlers:
    '''Signal handlers for indexing :class:`Work` records when
    related records are saved or deleted.'''

    @staticmethod
    def creatortype_save(sender, instance=None, raw=False, **_kwargs):
        '''reindex all associated works when a creator type is changed'''
        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        # if any members are associated
        works = Work.objects.filter(creator__creator_type__pk=instance.pk)
        if works.exists():
            logger.debug('creator type save, reindexing %d related works',
                         works.count())
            ModelIndexable.index_items(works)

    @staticmethod
    def creatortype_delete(sender, instance, **_kwargs):
        '''reindex all associated works when a creator type is deleted'''
        work_ids = Work.objects.filter(creator__creator_type__pk=instance.pk) \
                               .values_list('id', flat=True)
        if work_ids:
            logger.debug('creator type delete, reindexing %d related works',
                         len(work_ids))
            # find the items based on the list of ids to reindex
            works = Work.objects.filter(id__in=list(work_ids))
            ModelIndexable.index_items(works)

    @staticmethod
    def person_save(sender, instance=None, raw=False, **_kwargs):
        '''reindex all works associated via creator when a person is saved'''
        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        # if any members are associated
        works = Work.objects.filter(creator__person__pk=instance.pk)
        if works.exists():
            logger.debug('person save, reindexing %d related works',
                         works.count())
            ModelIndexable.index_items(works)

    @staticmethod
    def person_delete(sender, instance, **_kwargs):
        '''reindex all works associated via creator when a person is deleted'''
        work_ids = Work.objects.filter(creator__person__pk=instance.pk) \
                               .values_list('id', flat=True)
        if work_ids:
            logger.debug('person delete, reindexing %d related works',
                         len(work_ids))
            # find the items based on the list of ids to reindex
            works = Work.objects.filter(id__in=list(work_ids))
            ModelIndexable.index_items(works)

    @staticmethod
    def creator_change(sender, instance=None, raw=False, **_kwargs):
        '''reindex associated work when a creator record is changed'''
        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        logger.debug('creator change, reindexing %s',
                     instance.work)
        # delete the assocation so cards will index without the account
        ModelIndexable.index_items([instance.work])

    @staticmethod
    def format_save(sender, instance=None, raw=False, **_kwargs):
        '''reindex associated work when a format is changed'''
        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        # if any works are associated
        works = Work.objects.filter(work_format__pk=instance.pk)
        if works.exists():
            logger.debug('format save, reindexing %d related works',
                         works.count())
            ModelIndexable.index_items(works)

    @staticmethod
    def format_delete(sender, instance, **_kwargs):
        '''reindex all associated works when a format is deleted'''
        work_ids = Work.objects.filter(work_format__pk=instance.pk) \
                               .values_list('id', flat=True)
        if work_ids:
            logger.debug('format delete, reindexing %d related works',
                         len(work_ids))
            # find the items based on the list of ids to reindex
            works = Work.objects.filter(id__in=list(work_ids))
            ModelIndexable.index_items(works)


class Work(Notable, ModelIndexable):
    '''Work record for an item that circulated in the library or was
    other referenced in library activities.'''

    #: mep id from stub records imported from xml
    mep_id = models.CharField(
        max_length=255, blank=True, unique=True,
        verbose_name='MEP ID', null=True)
    # NOTE: mep_id has null=true so we can enforce unique constraint but
    # allow for items with no mep id

    title = models.CharField(
        max_length=255, blank=True,
        help_text='Title of the work in English')
    year = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name='Date of Publication')
    uri = models.URLField(blank=True, verbose_name='Work URI',
                          help_text="Linked data URI for this work")
    edition_uri = models.URLField(
        blank=True, verbose_name='Edition URI',
        help_text="Linked data URI for this edition, if known")
    ebook_url = models.URLField(
        blank=True, verbose_name='eBook URL',
        help_text='Link to a webpage where one or more ebook versions can be \
            downloaded, e.g. Project Gutenberg page for this item')
    work_format = models.ForeignKey(
        Format, verbose_name='Format', null=True, blank=True,
        help_text='Format, e.g. book or periodical', on_delete=models.SET_NULL)

    #: update timestamp
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # direct access to all creator persons, using Creator as through model
    creators = models.ManyToManyField(Person, through='Creator')

    #: optional genres, from OCLC record
    genres = models.ManyToManyField(Genre, blank=True,
                                    help_text='Genre(s) from OCLC record')
    #: optional subjects, from OCLC record
    subjects = models.ManyToManyField(Subject, blank=True)
    #: a field for notes publicly displayed on the website
    public_notes = models.TextField(
        blank=True, help_text='Notes for display on the public website')

    def save(self, *args, **kwargs):
        # override save to ensure mep ID is None rather than empty string
        # if not set
        if not self.mep_id:
            self.mep_id = None
        super(Work, self).save(*args, **kwargs)

    def __repr__(self):
        # provide pk for easy lookup and string for recognition
        return '<Work pk:%s %s>' % (self.pk or '??', str(self))

    def __str__(self):
        year_str = ''
        if self.year:
            year_str = '(%s)' % self.year
        str_value = ('%s %s' % (self.title, year_str)).strip()
        if str_value:
            return str_value
        return '(No title, year)'

    def creator_by_type(self, creator_type):
        '''return work creators of a single type, e.g. author'''
        return [creator.person for creator in self.creator_set.all()
                if creator.creator_type.name == creator_type]

    @property
    def creator_names(self):
        '''list of all creator names, including authors'''
        return [creator.name for creator in self.creators.all()]

    @property
    def authors(self):
        '''work creators with type author'''
        return self.creator_by_type('Author')

    def author_list(self):
        '''semicolon separated list of author names'''
        return '; '.join([auth.name for auth in self.authors])
    author_list.verbose_name = 'Authors'

    @property
    def sort_author_list(self):
        '''semicolon separated list of author sort names'''
        return '; '.join([auth.sort_name for auth in self.authors])

    @property
    def editors(self):
        '''work creators with type editor'''
        return self.creator_by_type('Editor')

    @property
    def translators(self):
        '''work creators with type translator'''
        return self.creator_by_type('Translator')

    @property
    def event_count(self):
        '''Number of events of any kind associated with this work.'''
        # use database annotation if present; otherwise use queryset
        return getattr(self, 'event__count',
                       self.event_set.count())

    @property
    def borrow_count(self):
        '''Number of times this work was borrowed.'''
        # use database annotation if present; otherwise use queryset
        return getattr(self, 'event__borrow__count',
                       self.event_set.filter(borrow__isnull=False).count())

    @property
    def purchase_count(self):
        '''Number of times this work was purchased.'''
        # use database annotation if present; otherwise use queryset
        return getattr(self, 'event__purchase__count',
                       self.event_set.filter(purchase__isnull=False).count())

    def admin_url(self):
        '''URL to edit this record in the admin site'''
        return reverse('admin:books_work_change', args=[self.id])
    admin_url.verbose_name = 'Admin Link'

    def has_uri(self):
        '''Is the URI is set for this work?'''
        return self.uri != ''
    has_uri.boolean = True
    has_uri.admin_order_field = 'uri'

    def subject_list(self):
        '''semicolon separated list of subject names'''
        return '; '.join([subj.name for subj in self.subjects.all()])

    def genre_list(self):
        '''semicolon separated list of genres'''
        return '; '.join([genre.name for genre in self.genres.all()])

    def format(self):
        '''format of this work if known (e.g. book or periodical)'''
        return self.work_format.name if self.work_format else ''

    index_depends_on = {
        'creators': {
            'post_save': WorkSignalHandlers.person_save,
            'pre_delete': WorkSignalHandlers.person_delete,
        },
        'books.Creator': {
            'post_save': WorkSignalHandlers.creator_change,
            'post_delete': WorkSignalHandlers.creator_change,
        },
        'books.CreatorType': {
            'post_save': WorkSignalHandlers.creatortype_save,
            'pre_delete': WorkSignalHandlers.creatortype_delete,
        },
        'books.Format': {
            'post_save': WorkSignalHandlers.format_save,
            'pre_delete': WorkSignalHandlers.format_delete,
        }
    }

    def index_data(self):
        '''data for indexing in Solr'''

        index_data = super().index_data()

        index_data.update({
            'title_t': self.title,
            'sort_title_isort': self.title, # use title directly for sorting for now
            'pk_i': self.pk, # NOTE include pk for now for item detail url
            'authors_t': [str(a) for a in self.authors] if self.authors else None,
            'sort_authors_isort': self.sort_author_list,
            'creators_t': self.creator_names,
            'pub_date_i': self.year,
            'format_s_lower': self.format(),
            'notes_txt_en': self.public_notes
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

        # add associations for genres, creating if necessary
        for genre in worldcat_entity.genres:
            self.genres.add(Genre.objects.get_or_create(name=genre)[0])

        # types will be prepopulated to work with OCLC search results
        # (predominantly books and periodicals), but in future
        # we may need a method to create format from uri as for subjects
        if worldcat_entity.item_type:
            print('entity item type %s' % worldcat_entity.item_type)
            try:
                self.work_format = Format.objects.get(
                    uri=worldcat_entity.item_type)
            except ObjectDoesNotExist:
                logger.error('Unexpected item type %s',
                             worldcat_entity.item_type)

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


class Edition(Notable):
    '''A specific known edition of a :class:`Work` that circulated.'''

    work = models.ForeignKey(
        Work, help_text='Generic Work associated with this edition.',
        on_delete=models.CASCADE)
    title = models.CharField(
        max_length=255, blank=True,
        help_text='Title of this edition, if different from associated work')
    volume = models.PositiveSmallIntegerField(blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True,
        help_text='Date of Publication for this edition')
    date_precision = DatePrecisionField(blank=True, null=True)
    partial_date = PartialDate('date', 'date_precision',
        PartialDateMixin.UNKNOWN_YEAR, label='publication date')
    season = models.CharField(max_length=255, blank=True,
        help_text='Spell out month or season if part of numbering')
    edition = models.CharField(max_length=255, blank=True)
    uri = models.URLField(
        blank=True, verbose_name='URI',
        help_text="Linked data URI for this edition, if known")

    #: update timestamp
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # direct access to all creator persons, using Creator as through model
    creators = models.ManyToManyField(Person, through='EditionCreator')

    publisher = models.ManyToManyField(Publisher, blank=True)
    pub_places = models.ManyToManyField(
        PublisherPlace, blank=True, verbose_name="Places of Publication")

    # language model foreign key may be added in future

    class Meta:
        ordering = ['date']

    def __repr__(self):
        # provide pk for easy lookup and string for recognition
        return '<Edition pk:%s %s>' % (self.pk or '??', self)

    def __str__(self):
        # simple string representation
        parts = [
            self.title or self.work.title or '??',
            '(%s)' % (self.partial_date or self.work.year or '??', ),
        ]
        if self.volume:
            parts.append('vol. %s' % self.volume)
        if self.number:
            parts.append('no. %s' % self.number)
        if self.season:
            parts.append(self.season)
        # include edition?
        return ' '.join(parts)

    def display_html(self):
        '''Render volume/issue citation with formatting, suitable
        for inclusion on a webpage.'''
        parts = []
        if self.volume:
            parts.append('Vol. %s' % self.volume)
        if self.number:
            parts.append('no. %s' % self.number)
        if self.season or self.date:
            season_year = '%s %s' % (
                self.season,
                self.date.year if self.date else '')
            parts.append(season_year.strip())

        citation = ', '.join(parts)

        if self.title:
            return format_html('{} <br/><em>{}</em>',
                               citation, self.title)
        return citation

    def display_text(self):
        '''text-only version of volume/issue citation'''
        return strip_tags(self.display_html())


class CreatorType(Named, Notable):
    '''Type of creator role a person can have in relation to a work;
    author, editor, translator, etc.'''


class Creator(Notable):
    creator_type = models.ForeignKey(CreatorType, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    work = models.ForeignKey(Work, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s %s' % (self.person, self.creator_type, self.work)


class EditionCreator(Notable):
    '''Creator specific to an :class:`Edition` of a :class:`Work`.'''

    creator_type = models.ForeignKey(CreatorType, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)

    def __str__(self):
        '''String representation: person, creator type, edition.'''
        return '%s %s %s' % (self.person, self.creator_type, self.edition)
