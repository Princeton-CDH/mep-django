from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
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


class Location(Notable):
    '''Locations for addresses associated with people and accounts'''
    #: optional name of the location (e.g., hotel)
    name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Name of location',
        help_text=('Name of the place if there is one, e.g. Savoy Hotel, '
                   'British Embassy, Villa Trianon')
    )
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
        unique_together = (("name", "street_address", "city", "country"),)

    def __repr__(self):
        return '<Location %s>' % self.__dict__

    def __str__(self):
        str_parts = [self.name, self.street_address, self.city]
        return ', '.join([part for part in str_parts if part])


class Profession(Named, Notable):
    '''Profession for a :class:`Person`'''
    pass


class PersonQuerySet(models.QuerySet):

    @transaction.atomic
    def merge_with(self, person):
        '''Merge all person records in the current queryset with the
        specified person.  This entails the following:
            - all events from accounts associated with people in the
              queryset are reassociated with the specified person
            - all addresses associated with people in the
              queryset or their accounts are reassociated with the
              specified person or their account
            - TODO: copy other details and update other relationships
            - after data has been copied over, people in the queryset and
              their accounts will be deleted

        Raises an error if the specified person has more than one
        account or if any people in the queryset have an account associated
        with another person.
        '''

        # error if person has no account
        # NOTE: could allow if nopeople in the queryset have accounts ...
        if not person.account_set.exists():
            raise ObjectDoesNotExist("Can't merge with a person record that has no account.")
        # error if more than account, since we can't pick which to merge to
        if person.account_set.count() > 1:
            raise MultipleObjectsReturned("Can't merge with a person record that has multiple accounts.")
        primary_account = person.account_set.first()

        # TODO: error if any accounts have more than one person associated

        # make sure specified person is skipped even if in the current queryset
        merge_people = self.exclude(id=person.id)

        for merge_person in merge_people:
            for account in merge_person.account_set.all():
                # reassociate all events with the main account
                account.event_set.update(account=primary_account)
                # reassociate any addresses with the main account
                account.address_set.update(account=primary_account)
                # delete the empty account
                account.delete()

            # update main person record with optional properties set on
            # the copy if not already present on the main record
            for attr in ['title', 'mep_id', 'birth_year', 'death_year',
                         'viaf_id', 'sex', 'profession']:
                # if not set on main person and set on merge person, copy
                if not getattr(person, attr) and getattr(merge_person, attr):
                    setattr(person, attr, getattr(merge_person, attr))
            # append any notes
            person.notes = '\n'.join(notes for notes in
                [person.notes, merge_person.notes] if notes)
            # reassociate related person data
            # - personal addresses
            merge_person.address_set.update(person=person)
            # - nationalities
            person.nationalities.add(*list(merge_person.nationalities.all()))
            # - relations
            merge_person.from_relationships.update(from_person=person)
            merge_person.to_relationships.update(to_person=person)
            # - info urls
            merge_person.urls.update(person=person)
            # - footnotes
            merge_person.footnotes.update(object_id=person.id)

        # delete the now-obsolete person records
        merge_people.delete()
        # save any attribute changes
        person.save()


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
    #: relationships to other people, via :class:`Relationship`
    relations = models.ManyToManyField(
        'self',
        through='Relationship',
        symmetrical=False
    )
    #: footnotes (:class:`~mep.footnotes.models.Footnote`)
    footnotes = GenericRelation(Footnote)

    # convenience access to associated locations, although
    # we will probably use Address for most things
    locations = models.ManyToManyField(Location, through='accounts.Address',
        blank=True, through_fields=('person', 'location'))

    # override default manager with customized version
    objects = PersonQuerySet.as_manager()

    def __repr__(self):
        return '<Person %s>' % self.__dict__

    def __str__(self):
        '''String representation; use sort name if available with fall back
        to name'''
        # if not sort name, return name with title in front
        # NOTE: strip is there to grab extra space and comma if no title
        if not self.sort_name:
            return ('%s %s' % (self.title, self.name)).strip()
        # if name sort_name and it's last, first, title goes after
        if self.sort_name and len(self.sort_name.split(',')) > 1:
            return ('%s, %s' % (self.sort_name, self.title)).strip(', ')
        # otherwise, append it to the front for most natural format
        else:
            return ('%s %s' % (self.title, self.sort_name)).strip(', ')

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

    def list_nationalities(self):
        '''Return comma separated list of nationalities (if any) for :class:`Person` list_view.'''
        nationalities = self.nationalities.all().order_by('name')
        if nationalities.exists():
            return ', '.join(country.name for country in nationalities)
        return ''
    list_nationalities.short_description = 'Nationalities'
    list_nationalities.admin_order_field = 'nationalities__name'

    def address_count(self):
        '''Number of documented addresses for this person'''
        # used in admin list view
        return self.address_set.count()
    address_count.short_description = '# Addresses'

    def has_account(self):
        '''Return whether an instance of :class:`mep.accounts.models.Account` exists for this person.'''
        return self.account_set.exists()
    has_account.boolean = True

    def in_logbooks(self):
        '''is there data for this person in the logbooks?'''
        # based on presense of subscription or reimbursement event
        return self.account_set.filter(
            models.Q(event__subscription__isnull=False) |
            models.Q(event__reimbursement__isnull=False)
            ).exists()
    in_logbooks.boolean = True


class InfoURL(Notable):
    '''Informational urls (other than VIAF) associated with a :class:`Person`,
    e.g. Wikipedia page.'''
    url = models.URLField(verbose_name='URL',
        help_text='Additional (non-VIAF) URLs for a person.')
    person = models.ForeignKey(Person, related_name='urls')

    class Meta:
        verbose_name = 'Informational URL'

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
