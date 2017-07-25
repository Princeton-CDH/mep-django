
from django.db import models

from mep.common.models import AliasIntegerField, DateRange, Named, Notable
from mep.common.validators import verify_latlon

class Country(Named):
    '''Countries, for documenting nationalities of a :class:`Person`'''
    code = models.CharField(max_length=3, unique=True,
        help_text='ISO two-letter country code')
    # TODO: should we enforce lower case to keep consistent?

    class Meta:
        verbose_name_plural = 'countries'


class Address(Notable):
    '''Addresses associated with accounts in the MEP database'''
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city_town = models.CharField(max_length=255, blank=True)
    # CharField for UK Addresses
    postal_code = models.CharField(max_length=25, blank=True)
    # NOTE: Using decimal field here to set precision on the head
    # FloatField uses float, which can introduce unexpected rounding.
    # This would let us have measurements down to the tree level, if necessary
    latitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        blank=True,
        null=True,
        validators=[verify_latlon]
    )
    longitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        blank=True,
        null=True,
        validators=[verify_latlon]
    )
    country = models.ForeignKey(Country, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'addresses'

    def __re__(self):
        return '<Address %s>' % self.__dict__

    def __str__(self):
        return ', '.join([part for part in [self.address_line_1, self.address_line_2, self.city_town] if part])

        if self.address_line_1 or self.city_town:
            return('%s, %s' %
                   (self.address_line_1, self.city_town)).strip(', ')
        else:
            return('Address, no street or city given')


class Profession(Named, Notable):
    '''Profession for a :class:`Person`'''
    pass



class Person(Notable, DateRange):
    '''Model for people in the MEP dataset'''

    #: MEP xml id
    mep_id = models.CharField('MEP id', max_length=255, blank=True,
        help_text='Identifier from XML personography')
    #: optional first name
    first_name = models.CharField(max_length=255, blank=True)
    #: last name
    last_name = models.CharField(max_length=255)
    #: viaf identifiers
    viaf_id = models.URLField('VIAF id', blank=True)
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
    #: known addresses, link to :class:`Address1
    addresses = models.ManyToManyField(Address, blank=True)
    #: relationships to other people, via :class:`Relationship`
    relations = models.ManyToManyField(
        'self',
        through='Relationship',
        symmetrical=False
    )

    def __repr__(self):
        return '<Person %s>' % self.__dict__

    def __str__(self):
        entry_name = '%s, %s' % (self.last_name, self.first_name)
        return entry_name.strip()

    @property
    def full_name(self):
        return ('%s %s' % (self.first_name, self.last_name)).strip()

    class Meta:
        verbose_name_plural = 'people'
        ordering = ['last_name', 'first_name']


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


class Relationship(models.Model):
    '''Through model for :class:`Person` to ``self``'''
    from_person = models.ForeignKey(Person, related_name='from_person')
    to_person = models.ForeignKey(Person, related_name='to_person')
    relationship_type = models.ForeignKey(RelationshipType)

    def __repr__(self):
        '''Custom method to produce a more human useable representation
        than dict in this case
        '''
        return ("<Relationship {'from_person': <Person %s>, "
                "'to_person': <Person %s>, 'relationship_type': "
                "<RelationshipType %s>}>") % (self.from_person.full_name,
                                              self.to_person.full_name,
                                              self.relationship_type.name)

    def __str__(self):
        return '%s is a %s to %s.' % (
            self.from_person.full_name,
            self.relationship_type.name,
            self.to_person.full_name
            )




