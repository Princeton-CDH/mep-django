import datetime

from django.db import models
from django.urls import reverse
from parasolr.indexing import Indexable

from mep.common.models import Named, Notable
from mep.common.validators import verify_latlon
from mep.people.models import Person


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
    pass


class Item(Notable, Indexable):
    '''Primary model for :mod:`books` module, also used for journals,
    and other media types.'''
    #: mep id from stub records imported from xml
    mep_id = models.CharField(max_length=255, blank=True, unique=True,
        verbose_name='MEP ID', null=True)
    # NOTE: mep_id has null=true so we can enforce unique constraint but
    # allow for items with no mep id

    title = models.CharField(max_length=255, blank=True)
    volume = models.PositiveSmallIntegerField(blank=True, null=True)
    number = models.PositiveSmallIntegerField(blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True,
        verbose_name='Date of Publication')
    season = models.CharField(max_length=255, blank=True)
    edition = models.CharField(max_length=255, blank=True)
    uri = models.URLField(blank=True, verbose_name='URI', help_text="Linked data URI for this work")

    #: update timestamp
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # QUESTION: On the diagram these are labeled as FK, but they seem to imply
    # M2M (i.e. more than one publisher or more than one pub place?)
    publishers = models.ManyToManyField(Publisher, blank=True)
    pub_places = models.ManyToManyField(PublisherPlace, blank=True, verbose_name="Places of Publication")

    # direct access to all creator persons, using Creator as through model
    creators = models.ManyToManyField(Person, through='Creator')

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
        '''comma separated list of author names'''
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
    def first_known_interaction(self) -> datetime.date:
        '''date of the earliest known interaction for this item'''
        first_event = self.event_set \
            .filter(start_date__isnull=False) \
            .order_by('start_date').first()

        # TODO: does not currently filter out dates with unknown years
        if first_event:
            return first_event.start_date


class CreatorType(Named, Notable):
    '''Type of creator role a person can have to an item; author,
    editor, translator, etc.'''
    pass

class Creator(Notable):
    creator_type = models.ForeignKey(CreatorType)
    person = models.ForeignKey(Person)
    item = models.ForeignKey(Item)

    def __str__(self):
        return '%s %s %s' % (self.person, self.creator_type, self.item)