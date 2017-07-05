from django.db import models
from mep.common.models import Named, Notable
from mep.common.validators import verify_latlon


class Item(Notable):
    '''Primary model for Books module, also used for journals, etc.'''
    mep_id = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    volume = models.PositiveSmallIntegerField(blank=True, null=True)
    number = models.PositiveSmallIntegerField(blank=True, null=True)
    year = models.PositiveSmallIntegerField(
        validators=[valid_year],
        blank=True,
        null=True
    )
    season = models.CharField(max_length=255, blank=True)
    edition = models.CharField(max_length=255, blank=True)
    viaf_id = models.URLField(blank=True)
    # Creator fields - three M2Ms to people
    authors = models.ManyToManyField('people.Person', related_name='authors')
    editors = models.ManyToManyField('people.Person', related_name='editors')
    translators = models.ManyToManyField('people.Person',
                                         related_name='translators')
    # QUESTION: On the diagram these are labeled as FK, but they seem to imply
    # M2M (i.e. more than one publisher or more than one pub place?)
    publishers = models.ManyToManyField('Publisher', blank=True)
    pub_places = models.ManyToManyField('PublisherPlace', blank=True)

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
