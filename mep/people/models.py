from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from viapy.api import ViafEntity

from mep.common.models import AliasIntegerField, DateRange, Named, Notable
from mep.common.validators import verify_latlon
from mep.footnotes.models import Footnote


class Country(Named):
    '''Countries, for documenting nationalities of a :class:`Person`
    or location of an :class:`Address`'''
    geonames_id = models.URLField('GeoNames ID', unique=True, blank=True,
        help_text='GeoNames identifier')
    code = models.CharField('Country Code', unique=True, blank=True,
        help_text='Two-letter country code', max_length=2)
    # id & code are optional to support no country/stateless

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ('name',)


class Address(Notable):
    '''Addresses associated with people and accounts'''
    #: optional name of the location (e.g., hotel)
    name = models.CharField(max_length=255, blank=True)
    #: street address
    street_address = models.CharField(max_length=255, blank=True)
    #: city or town
    city = models.CharField(max_length=255)
    #: postal code; character rather than integer to support
    # UK addresses and other non-numeric postal codes
    postal_code = models.CharField(max_length=25, blank=True)
    # NOTE: Using decimal field here to set precision on the head
    # FloatField uses float, which can introduce unexpected rounding.
    # This would let us have measurements down to the tree level, if necessary
    #: latitude
    latitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        blank=True,
        null=True,
        validators=[verify_latlon]
    )
    #: longitude
    longitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        blank=True,
        null=True,
        validators=[verify_latlon]
    )
    #: :class:`Country`
    country = models.ForeignKey(Country, blank=True, null=True)

    #: footnotes (:class:`~mep.footnotes.models.Footnote`)
    footnotes = GenericRelation(Footnote)


    class Meta:
        verbose_name_plural = 'addresses'

    def __repr__(self):
        return '<Address %s>' % self.__dict__

    def __str__(self):
        str_parts = [self.name, self.street_address, self.city]
        return ', '.join([part for part in str_parts if part])


class Profession(Named, Notable):
    '''Profession for a :class:`Person`'''
    pass



class Person(Notable, DateRange):
    '''Model for people in the MEP dataset'''

    #: MEP xml id
    mep_id = models.CharField('MEP id', max_length=255, blank=True,
        help_text='Identifier from XML personography')
    #: names (first middle last)
    name = models.CharField(max_length=255,
        help_text='''Name as firstname lastname, firstname (birthname) married name,
        or psuedonym (real name)''')
    #: sort name; authorized name for people with VIAF
    sort_name = models.CharField(max_length=255,
        help_text='Sort name in lastname, firstname format; VIAF authorized name if available')
    #: viaf identifiers
    viaf_id = models.URLField('VIAF id', blank=True,
        help_text='Canonical VIAF URI for this person')
    #: birth year
    birth_year = AliasIntegerField(db_column='start_year',
        blank=True, null=True)
    #: death year
    death_year = AliasIntegerField(db_column='end_year',
        blank=True, null=True)

    MALE = 'M'
    FEMALE = 'F'
    SEX_CHOICES = (
        (FEMALE, 'Female'),
        (MALE, 'Male'),
    )
    #: sex
    sex = models.CharField(blank=True, max_length=1, choices=SEX_CHOICES)
    #: title
    title = models.CharField(blank=True, max_length=255)
    #: :class:`Profession`
    profession = models.ForeignKey(Profession, blank=True, null=True)
    #: nationalities, link to :class:`Country`
    nationalities = models.ManyToManyField(Country, blank=True)
    #: known addresses, many-to-many link to :class:`Address`
    addresses = models.ManyToManyField(Address, blank=True)
    #: relationships to other people, via :class:`Relationship`
    relations = models.ManyToManyField(
        'self',
        through='Relationship',
        symmetrical=False
    )

    #: footnotes (:class:`~mep.footnotes.models.Footnote`)
    footnotes = GenericRelation(Footnote)

    def __repr__(self):
        return '<Person %s>' % self.__dict__

    def __str__(self):
        '''String representation; use sort name if available with fall back
        to name'''
        return self.sort_name or self.name

    class Meta:
        verbose_name_plural = 'people'
        ordering = ['sort_name']

    def save(self, *args, **kwargs):
        '''Adds birth and death dates if they aren't already set
        and there's a viaf id for the record'''

        if self.viaf_id and not self.birth_year and not self.death_year:
            self.set_birth_death_years()

        super(Person, self).save(*args, **kwargs)

    @property
    def viaf(self):
        ''':class:`viapy.api.ViafEntity` for this record if :attr:`viaf_id`
        is set.'''
        if self.viaf_id:
            return ViafEntity(self.viaf_id)

    def set_birth_death_years(self):
        '''Set local birth and death dates based on information from VIAF'''
        if self.viaf_id:
            self.birth_year = self.viaf.birthyear
            self.death_year = self.viaf.deathyear


class InfoURL(Notable):
    '''Informational urls (other than VIAF) associated with a :class:`Person`,
    e.g. Wikipedia page.'''
    url = models.URLField(
        help_text='Additional (non-VIAF) URLs for a person.')
    person = models.ForeignKey(Person, related_name='urls')

    def __repr__(self):
        return "<InfoURL %s>" % self.__dict__

    def __str__(self):
        return self.url


class RelationshipType(Named, Notable):
    '''Types of relationships between one :class:`Person` and another'''
    pass


class Relationship(Notable):
    '''Through model for :class:`Person` to ``self``'''
    from_person = models.ForeignKey(Person, related_name='from_relationships')
    to_person = models.ForeignKey(Person, related_name='to_relationships')
    relationship_type = models.ForeignKey(RelationshipType)

    def __repr__(self):
        '''Custom method to produce a more human useable representation
        than dict in this case
        '''
        return ("<Relationship {'from_person': <Person %s>, "
                "'to_person': <Person %s>, 'relationship_type': "
                "<RelationshipType %s>}>") % (self.from_person.name,
                                              self.to_person.name,
                                              self.relationship_type.name)

    def __str__(self):
        return '%s is a %s to %s.' % (
            self.from_person.name,
            self.relationship_type.name,
            self.to_person.name
            )




