import logging

from django.apps import apps
from django.core.exceptions import MultipleObjectsReturned
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from parasolr.django.indexing import ModelIndexable
from viapy.api import ViafEntity

from mep.common.models import AliasIntegerField, DateRange, Named, Notable
from mep.common.validators import verify_latlon
from mep.footnotes.models import Footnote


logger = logging.getLogger(__name__)


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
        return '<Location pk:%s %s>' % (self.pk or '??', str(self))

    def __str__(self):
        str_parts = [self.name, self.street_address, self.city]
        return ', '.join([part for part in str_parts if part])


class Profession(Named, Notable):
    '''Profession for a :class:`Person`'''


class PersonQuerySet(models.QuerySet):
    '''Custom :class:`models.QuerySet` for :class:`Person`'''

    def library_members(self):
        '''Rsestrict queryset to people who are library members,
        based on assocatide account.'''
        return self.exclude(account=None)

    @transaction.atomic
    def merge_with(self, person):
        '''Merge all person records in the current queryset with the
        specified person. This entails the following:

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

        :param person: :class:`Person` person
        :raises django.core.exceptions.MultipleObjectsReturned:
            if selected :class:`Person` has multiple accounts _or_ any person
            in the queryset has an account shared with another person
        '''

        # identify the account other events will be reassociated with, if exists
        primary_account = None
        if person.has_account():
            primary_account = person.account_set.first()
        # error if more than account, since we can't pick which to merge to
        if person.account_set.count() > 1:
            raise MultipleObjectsReturned("Can't merge with a person record that has multiple accounts.")
        # error if any accounts have more than one person associated
        if self.annotate(account_people=models.Count('account__persons')) \
               .filter(account_people__gt=1).exists():
            raise MultipleObjectsReturned("Can't merge a person record with a shared account.")

        # make sure specified person is skipped even if in the current queryset
        merge_people = self.exclude(id=person.id)

        Creator = apps.get_model('books', 'Creator') # prevents circular import issue

        for merge_person in merge_people:
            if merge_person.has_account(): # if the merged person had an account

                # store primary account card reference if there is one
                account_card = primary_account.card if primary_account else None

                for account in merge_person.account_set.all():

                    # if the account to be merged has an associated library card
                    if account.card:
                        # store the first account card reference we find,
                        # if we don't already have one
                        if not account_card:
                            account_card = account.card
                        else:
                            # unlikely, but if we're merging two accounts with cards
                            # log a warning so we can track it down later if necessary
                            logger.warning('Account %s card %s association will be lost in merge',
                                            account, account.card)

                    # if a merge person has an account, but the main person doesn't,
                    # swap the account's owner to the main person
                    if not person.has_account():
                        account.persons.add(person)
                        account.persons.remove(merge_person)
                         # define the new primary account
                        primary_account = person.account_set.first()
                    else:
                        account.event_set.update(account=primary_account) # reassociate all events with the main account
                        account.address_set.update(account=primary_account) # reassociate any addresses with the main account
                        account.delete() # delete the empty account

                # if a card was present on the account to be merged and *not*
                # on the primary account, copy it
                if not primary_account.card and account_card:
                    primary_account.card = account_card
                    primary_account.save()

            if merge_person.is_creator(): # if the merged person was a creator
                for creator in merge_person.creator_set.all():
                    creator.person = person # reassociate the creator relationship to the primary person
                    creator.save()

            # update main person record with optional properties set on
            # the copy if not already present on the main record
            for attr in ['title', 'mep_id', 'birth_year', 'death_year',
                         'viaf_id', 'sex', 'profession']:
                # if not set on main person and set on merge person, copy
                if not getattr(person, attr) and getattr(merge_person, attr):
                    setattr(person, attr, getattr(merge_person, attr))
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

        # consolidate notes and preserve any merged MEP ids
        # in case we need to find a record based on a deleted MEP id
        # (e.g. for card import)
        # get current date to record when this merge happened
        iso_date = timezone.now().strftime('%Y-%m-%d')
        notes = [person.notes]
        notes.extend([p.notes for p in merge_people])
        notes.extend(['Merged MEP id %s on %s' % (person.mep_id, iso_date)
                      for person in merge_people if person.mep_id])
        notes.extend(['Merged %s on %s' % (person.name, iso_date)
                      for person in merge_people if not person.mep_id])
        person.notes = '\n'.join(note for note in notes if note)

        # delete the now-obsolete person records
        merge_people.delete()
        # save any attribute changes
        person.save()


class PersonSignalHandlers:
    '''Signal handlers for indexing :class:`Person` records when
    related records are saved or deleted.'''

    @staticmethod
    def nationality_save(sender, instance, **kwargs):
        if instance.pk:
            # if any members are associated
            members = instance.person_set.library_members().all()
            if members.exists():
                logger.debug('nationality save, reindexing %d related people',
                             members.count())
                ModelIndexable.index_items(members)

    @staticmethod
    def nationality_delete(sender, instance, **kwargs):
        logger.debug('nationality delete')
        # get a list of ids for collected works before clearing them
        person_ids = instance.person_set.library_members().values_list('id', flat=True)
        # find the items based on the list of ids to reindex
        members = Person.objects.filter(id__in=list(person_ids))

        # NOTE: this sends pre/post clear signal, but it's not obvious
        # how to take advantage of that
        instance.nationality_set.clear()
        ModelIndexable.index_items(members)


class Person(Notable, DateRange, ModelIndexable):
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
    #: flag to indicate organization instead of person
    is_organization = models.BooleanField(default=False,
        help_text='Check to indicate this entity is an organization rather than a person')
    #: verified flag
    verified = models.BooleanField(default=False,
        help_text='Check to indicate information in this record has been checked against the relevant archival sources.')
    #: update timestamp
    updated_at = models.DateTimeField(auto_now=True, null=True)

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
    #: a field for notes publicly displayed on the website
    public_notes = models.TextField(blank=True,
        help_text='Notes for display on the public site')

    # convenience access to associated locations, although
    # we will probably use Address for most things
    locations = models.ManyToManyField(Location, through='accounts.Address',
        blank=True, through_fields=('person', 'location'))

    # override default manager with customized version
    objects = PersonQuerySet.as_manager()

    def __repr__(self):
        return '<Person pk:%s %s>' % (self.pk or '??', self.sort_name)

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

    def get_absolute_url(self):
        '''
        Return the public url to view library member's detail page
        '''
        # NOTE: using pk temporarily until we add slugs
        if self.has_account():
            # Only people with accounts have member detail pages
            return reverse('people:member-detail', args=[self.pk])
        # for now returning no url for person with no account

    @property
    def viaf(self):
        ''':class:`viapy.api.ViafEntity` for this record if :attr:`viaf_id`
        is set.'''
        if self.viaf_id:
            return ViafEntity(self.viaf_id)

    @property
    def short_name(self):
        '''Shortened form of name used for locations where space is tight,
        e.g. breadcrumb navigation'''
        # return the initial portion, before parenthesis or a comma
        return self.sort_name.split(',')[0].split('(')[0].strip()

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

    def account_id(self):
        '''Return the id number of the person's associated
        :class:`~mep.accounts.models.Account` or empty string if not.'''
        # used in admin list view, assumes only one account but
        # uses M2M prior to refactor
        if self.account_set.exists():
            return self.account_set.first().id
        return ''

    def has_account(self):
        '''Return whether an instance of :class:`mep.accounts.models.Account` exists for this person.'''
        return self.account_set.exists()
    has_account.boolean = True

    def subscription_dates(self):
        '''Return a semi-colon separated list of
        :class:`mep.accounts.models.Subscription` instances associated with
        this person's account(s).'''

        if self.account_set.exists():
            subscriptions = self.account_set.first().event_set.subscriptions()
            # NOTE: This will return unknown year events first, followed by
            # actual years since presumably all correct years will follow 1900
            # as the value for UNKNOWN_YEAR
            return '; '.join([sub.date_range for sub in
                                subscriptions.order_by('start_date')])
        return ''

    def is_creator(self):
        '''Return whether this person is a :class:`mep.books.models.Creator` of an :class:`mep.books.models.Item` .'''
        return self.creator_set.exists()
    is_creator.boolean = True

    def in_logbooks(self):
        '''is there data for this person in the logbooks?'''
        # based on presense of subscription or reimbursement event
        return self.account_set.filter(
            models.Q(event__subscription__isnull=False) |
            models.Q(event__reimbursement__isnull=False)
            ).exists()
    in_logbooks.boolean = True

    def has_card(self):
        '''The library account for this person has an associated lending card'''
        return self.account_set.filter(card__isnull=False).exists()
    has_card.boolean = True

    def admin_url(self):
        '''URL to edit this record in the admin site'''
        return reverse('admin:people_person_change', args=[self.id])
    admin_url.verbose_name = 'Admin Link'

    index_depends_on = {
        'nationalities': {
            'save': PersonSignalHandlers.nationality_save,
            'delete': PersonSignalHandlers.nationality_delete,
        }
    }

    @classmethod
    def items_to_index(cls):
        '''Custom logic for finding items to be indexed when indexing in
        bulk; only include library members.'''
        return cls.objects.library_members()

    def index_data(self):
        '''data for indexing in Solr'''

        index_data = super().index_data()
        # only library members are indexed; if person has no
        # account, return id only.
        # This will blank out any previously indexed values, and item
        # will not be findable by any public searchable fields.
        if not self.has_account():
            del index_data['item_type']
            return index_data

        # get account membership dates
        account = self.account_set.first()

        index_data.update({
            'name_t': self.name,
            # include pk for now for member detail url
            'pk_i': self.pk,
            # text version of sort name for search and display
            'sort_name_t': self.sort_name,
            # string version of sort name for sort/facet
            'sort_name_sort_s': self.sort_name,
            'birth_year_i': self.birth_year,
            'death_year_i': self.death_year,
            'has_card_b': self.has_card(),
            'nationality': list(self.nationalities.all()
                                    .values_list('name', flat=True))
        })

        # conditionally set fields that are not always present
        # to avoid having None values stored in Solr
        account_dates = account.event_dates
        if account_dates:
            # convert dates to just years, use set to uniquify, and
            # convert back to list for json serialization to Solr
            account_years = list(set(date.year for date in account.event_dates))
            index_data.update({
                'account_years_is': account_years,
                # use min and max because set order is not guaranteed
                'account_start_i': min(account_years),
                'account_end_i': max(account_years),
            })
        if self.sex:
            index_data['sex_s'] = self.get_sex_display()
        return index_data


class InfoURL(Notable):
    '''Informational urls (other than VIAF) associated with a :class:`Person`,
    e.g. Wikipedia page.'''
    url = models.URLField(verbose_name='URL',
        help_text='Additional (non-VIAF) URLs for a person.')
    person = models.ForeignKey(Person, related_name='urls')

    class Meta:
        verbose_name = 'Informational URL'

    def __repr__(self):
        return "<InfoURL pk:%s %s>" % (self.pk or '??', self.url)

    def __str__(self):
        return self.url


class RelationshipType(Named, Notable):
    '''Types of relationships between one :class:`Person` and another'''


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
