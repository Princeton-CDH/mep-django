from django.db import models

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


class Item(Notable):
    '''Primary model for :mod:`books` module, also used for journals,
    and other media types.'''
    mep_id = models.CharField(max_length=255, blank=True, unique=True, verbose_name='MEP ID')
    title = models.CharField(max_length=255, blank=True)
    volume = models.PositiveSmallIntegerField(blank=True, null=True)
    number = models.PositiveSmallIntegerField(blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True,null=True, verbose_name='Date of Publication')
    season = models.CharField(max_length=255, blank=True)
    edition = models.CharField(max_length=255, blank=True)
    viaf_id = models.URLField(blank=True)

    # QUESTION: On the diagram these are labeled as FK, but they seem to imply
    # M2M (i.e. more than one publisher or more than one pub place?)
    publishers = models.ManyToManyField(Publisher, blank=True)
    pub_places = models.ManyToManyField(PublisherPlace, blank=True, verbose_name="Places of Publication")

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

    def authors(self):
        return Person.objects.filter(creator__item=self)

    def author_list(self):
        return ', '.join([str(auth) for auth in self.authors()])


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