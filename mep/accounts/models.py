# -*- coding: utf-8 -*-
import datetime
from itertools import chain

from cached_property import cached_property
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import ValidationError
from django.db import models
from django.db.models.functions import Coalesce
from django.template.defaultfilters import pluralize

from mep.accounts.partial_date import PartialDateMixin, DatePrecision,\
    DatePrecisionField
from mep.books.models import Work, Edition
from mep.common.models import Named, Notable
from mep.people.models import Person, Location
from mep.footnotes.models import Bibliography, Footnote


class Account(models.Model):
    '''Central model for all account and related information, M2M explicity to
    :class:`people.Person`'''

    persons = models.ManyToManyField(Person, blank=True,
        verbose_name='Account holder(s)')
    # convenience access to associated locations, although
    # we will probably use Address for most things
    locations = models.ManyToManyField(Location, through='Address', blank=True)

    card = models.ForeignKey(Bibliography, blank=True, null=True,
        help_text='Lending Library Card for this account',
        limit_choices_to={'source_type__name': 'Lending Library Card'},
        on_delete=models.SET_NULL)

    def __repr__(self):
        names = ''
        if self.pk and self.persons.count():
            names = ' %s' % \
                ';'.join([str(person) for person in self.persons.all()])

        return '<Account pk:%s%s>' % (self.pk or '??', names)

    def __str__(self):
        if not self.persons.exists() and not self.locations.exists():
            return 'Account #%s' % self.pk
        if self.persons.exists():
            return 'Account #%s: %s' % (
                self.pk,
                ', '.join(person.name for person in self.persons.all())
            )
        if self.locations.exists():
            return 'Account #%s: %s' % (
                self.pk,
                '; '.join(address.name if address.name else
                          address.street_address if address.street_address else
                          address.city for address in
                          self.locations.all().order_by(
                          'city', 'street_address', 'name'))
        )

    class Meta:
        ordering = ('persons__sort_name',)

    def list_persons(self):
        '''List :class:`mep.people.models.Person` instances associated with this
        account.
        '''
        return ', '.join(person.name for
                         person in self.persons.all().order_by('name'))
    list_persons.short_description = 'Account holder(s)'

    @property
    def event_dates(self):
        '''sorted list of all unique event dates associated with this account;
        ignores borrow and purchase dates with unknown year'''
        # get value list of all start and end dates
        date_values = self.event_set.known_years() \
            .values_list('start_date', 'end_date')
        # flatten list of tuples into a list, filter out None, and make unique
        uniq_dates = set(filter(None, chain.from_iterable(date_values)))
        # return as a sorted list
        return sorted(list(uniq_dates))

    def event_date_ranges(self, event_type=None):
        '''Generate and return a list of date ranges this account
        was active, based on associated events. Optionally filter
        to a specific kind of event activity (currently only
        supports membership).
        '''
        ranges = []
        current_range = None

        events = self.event_set.known_years() \
                               .annotate(
            first_date=Coalesce('start_date', 'end_date')
        ).order_by('first_date')

        # if event type was specified, filter as requested
        if event_type == 'membership':
            events = events.membership_activities()

        for event in events:
            # if no date is set, ignore
            if not event.start_date and not event.end_date:
                continue

            # if either date is partial with month unknown, skip
            if (event.start_date and event.start_date_precision and
               not event.start_date_precision.month) or \
               (event.end_date and event.end_date_precision and
               not event.end_date_precision.month):
                continue

            # if only one date is known, use for start/end of
            # range (i.e., borrow event with no end date)
            if not event.start_date or not event.end_date:
                date = event.start_date or event.end_date
                start_date = end_date = date

            # otherwise, use start and end dates for range
            else:
                start_date = event.start_date
                end_date = event.end_date

            # if no current range is set, create one from current event
            if not current_range:
                current_range = [start_date, end_date]
            # if this event starts within the current range, include it
            # NOTE: includes the following day; if this event is the
            # next day after the current range, extend the same range
            elif current_range[0] <= start_date <= \
                    (current_range[1] + datetime.timedelta(days=1)):
                current_range[1] = max(end_date, current_range[1])
            # otherwise, close out the current range and start a new one
            else:
                ranges.append(current_range)
                current_range = [start_date, end_date]

        # store the last range after the loop ends
        if current_range:
            ranges.append(current_range)
        return ranges

    def active_months(self, event_type=None):
        '''Generate and return a list of year/month dates this account
        was active, based on associated events. Optionally filter
        to a specific kind of event activity (currently supports
        "membership" or "books").
        Months are returned as a set in YYYYMM format.
        '''
        months = set()

        # Book activities are handled differently, since they do not
        # span multiple months; no need to convert to date ranges
        if event_type == 'books':
            book_events = self.event_set.known_years().book_activities()
            for event in book_events:
                # skip unset dates and unknown months (precision unset
                # or month flag present); add all other
                # to the set of years & months in YYYYMM format
                if event.start_date and \
                   (not event.start_date_precision or
                        event.start_date_precision.month):
                    months.add(event.start_date.strftime('%Y%m'))
                if event.end_date and \
                   (not event.end_date_precision or
                        event.end_date_precision.month):
                    months.add(event.end_date.strftime('%Y%m'))

            return months

        # For general events or membership activity,
        # calculate months based on date ranges to track months
        # when a subscription was active
        date_ranges = self.event_date_ranges(event_type)
        for start_date, end_date in date_ranges:
            current_date = start_date
            while current_date <= end_date:
                # if date is within range,
                # add to set of months in YYYYMM format
                months.add(current_date.strftime('%Y%m'))
                # get the date for the first of the next month
                next_month = current_date.month + 1
                year = current_date.year
                # handle december to january
                if next_month == 13:
                    year += 1
                    next_month = 1
                current_date = datetime.date(year, next_month, 1)
        return months

    def earliest_date(self):
        '''Earliest known date from all events associated with this account'''
        dates = self.event_dates
        if dates:
            return dates[0]

    def last_date(self):
        '''Last known date from all events associated with this account'''
        dates = self.event_dates
        if dates:
            return dates[-1]

    @property
    def subscription_set(self):
        '''associated subscription events, as queryset of
        :class:`Subscription`'''
        return Subscription.objects.filter(account_id=self.id)

    @property
    def reimbursement_set(self):
        '''
        associated reimbursement events, as queryset of :class:`Reimbursement`
        '''
        return Reimbursement.objects.filter(account_id=self.id)

    def list_locations(self):
        '''List of associated :class:`mep.people.models.Location` '''
        return '; '.join([str(loc) for loc in self.locations.distinct()])
    list_locations.short_description = 'Locations'

    def has_card(self):
        '''Account has an associated lending card'''
        return bool(self.card)
    has_card.boolean = True

    @staticmethod
    def validate_etype(etype):
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscription',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscription, or reimbursement')

    @staticmethod
    def str_to_model(etype):
        # moving mapping here so that we can forward reference classes
        # not yet declared
        mapping = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscription': Subscription
        }
        return mapping[etype]

    def add_event(self, etype='event', **kwargs):
        '''Helper function to add a :class:`Event` or subclass to an
        instance of :class:`Account`. Requires that the :class:`Account`
        object be saved first (so it has a set primary key).
        This provides functionality normally in the ``self.*_set``
        functionality of Django, but not provided with subclassed
        table inheritence.

       :param etype: ``str``
            One of ``borrow``, ``event``, ``subscription``,
            ``purchase``, ``reimbursement``
        '''
        # Catch an invalid class of event or subevent and raise
        # ValueError
        self.validate_etype(etype)
        # Create the event
        self.str_to_model(etype).objects.create(account=self, **kwargs)

    def get_events(self, etype='event', **kwargs):
        '''Helper function to retrieve related events of any valid type for
        :class:`Account.add_event()`. This provides functionality normally in the
        ``self.*_set`` functionality, but not provided with subclassed
        table inheritence.

        :param etype: ``str``
            One of ``borrow``, ``event``, ``subscription``,
            ``purchase``, ``reimbursement``

        :Keyword Arguments:
            Any valid query kwargs for :class:`Account`, defaults to equivalent
            of ``Foo.objects.all()``.

        '''
        # Catch an invalid class of event or subevent
        self.validate_etype(etype)
        return self.str_to_model(etype).objects.filter(account=self, **kwargs)


class Address(Notable, PartialDateMixin):
    '''Address associated with an :class:`Account` or
    a :class:`~mep.people.models.Person`.  Used to associate locations with
    people and accounts, with optional start and end dates and a care/of person.'''
    location = models.ForeignKey(Location)
    account = models.ForeignKey(Account, blank=True, null=True,
        help_text='Associated library account')
    person = models.ForeignKey(Person, blank=True, null=True,
        help_text='For personal addresses not associated with library accounts.')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    care_of_person = models.ForeignKey(Person, blank=True, null=True,
        related_name='care_of_addresses')

    class Meta:
        verbose_name_plural = 'Addresses'

    def __repr__(self):
        # use pk to make it easy to find again; string representation
        # for recognizability
        return '<Address pk:%s %s>' % (self.pk or '??', str(self))

    def __str__(self):
        details = self.account or self.person or ''
        if self.start_date or self.end_date:
            details = '%s (%s)' % (details, '-'.join([
                date.strftime('%Y') if date else ''
                for date in [self.start_date, self.end_date]]))
        if self.care_of_person:
            details = '%s c/o %s' % (details, self.care_of_person)

        # include details if there are any
        if details:
            return '%s - %s' % (self.location, details)
        # otherwise just location
        return str(self.location)

    def clean(self):
        '''Validate to require one and only one of :class:`Account` or
        :class:`~mep.people.models.Person`'''
        if not self.account and not self.person:
            raise ValidationError('Address must be associated with an account or person')
        if self.account and self.person:
            raise ValidationError('Address must only be associated with one of account or person')


class EventQuerySet(models.QuerySet):
    '''Custom :class:`~django.db.models.Queryset` for :class:`Event`
    with filter methods for generic events and each event subtype.'''

    def generic(self):
        '''Generic events only (excludes subscriptions, reimbursements,
        borrows, and purchases).'''
        return self.filter(subscription__isnull=True,
                           reimbursement__isnull=True,
                           borrow__isnull=True,
                           purchase__isnull=True)

    def _subtype(self, event_type):
        return self.filter(**{'%s__isnull' % event_type: False})

    def subscriptions(self):
        '''Events with associated subscription event only'''
        return self._subtype('subscription')

    def reimbursements(self,):
        '''Events with associated reimbursement event only'''
        return self._subtype('reimbursement')

    def borrows(self):
        '''Events with associated borrow event only'''
        return self._subtype('borrow')

    def purchases(self):
        '''Events with associated purchase event only'''
        return self._subtype('purchase')

    def membership_activities(self):
        '''Subscription and reimbursement events'''
        return self.filter(models.Q(subscription__isnull=False) |
                           models.Q(reimbursement__isnull=False))

    def book_activities(self):
        '''All events tied to a :class:`~mep.books.models.Work`.'''
        return self.filter(work__isnull=False)

    def known_years(self):
        '''Filter out any events with unknown years for start or
        end date.'''
        return self.exclude(start_date_precision__knownyear=False) \
                   .exclude(end_date_precision__knownyear=False)


class Event(Notable, PartialDateMixin):
    '''Base table for events in the Shakespeare and Co. Lending Library'''
    account = models.ForeignKey(Account)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    work = models.ForeignKey(
        Work, null=True, blank=True,
        help_text='Work associated with this event, if any.',
        on_delete=models.deletion.SET_NULL)
    edition = models.ForeignKey(
        Edition, null=True, blank=True,
        help_text='Edition of the work, if known.',
        on_delete=models.deletion.SET_NULL)

    event_footnotes = GenericRelation(Footnote, related_query_name='events')

    objects = EventQuerySet.as_manager()

    class Meta:
        # NOTE: ordering events by account person seems to be very slow
        # disabling for now
        # ordering = ('start_date', 'account__persons__sort_name')
        ordering = ('start_date', )

    def __repr__(self):
        '''Generic representation string for Event and subclasses'''
        return '<%s pk:%d account:%s %s>' % \
            (self.__class__.__name__, self.pk, self.account.pk,
             self.date_range)

    def __str__(self):
        '''Generic string method for Event and subclasses'''
        return '%s for account #%s %s' % \
            (self.__class__.__name__, self.account.pk, self.date_range)

    @cached_property
    def event_type(self):
        try:
            return self.subscription.get_subtype_display()
        except ObjectDoesNotExist:
            pass
        if getattr(self, 'reimbursement', None):
            return 'Reimbursement'
        if getattr(self, 'borrow', None):
            return 'Borrow'
        if getattr(self, 'purchase', None):
            return 'Purchase'
        return 'Generic'


class SubscriptionType(Named, Notable):
    '''Type of subscription'''


class CurrencyMixin(models.Model):
    '''Mixin for currency field with currency symbol display'''

    USD = 'USD'
    FRF = 'FRF'
    GBP = 'GBP'
    # NOTE: Preliminary currency set for now
    CURRENCY_CHOICES = (
        ('', '----'),
        (USD, 'US Dollar'),
        (FRF, 'French Franc'),
        (GBP, 'British Pound')
    )

    symbols = {
        FRF: '₣',
        USD: '$',
        GBP: '£'
    }

    currency = models.CharField(max_length=3, blank=True,
        choices=CURRENCY_CHOICES, default=FRF)

    class Meta:
        abstract = True

    def currency_symbol(self):
        '''symbol for the selected currency'''
        return self.symbols.get(self.currency, self.currency)
    # NOTE: could use ¤ (generic currency), but probably not that well known
    currency_symbol.short_description = '$'
    currency_symbol.admin_order_field = 'currency'


class Subscription(Event, CurrencyMixin):
    '''Records subscription events in the MEP database'''
    duration = models.PositiveIntegerField('Days',
        blank=True, null=True,
        help_text='Subscription duration in days. Automatically calculated from start and end date.')
    volumes = models.DecimalField(blank=True, null=True, max_digits=4,
        decimal_places=2,
        help_text='Number of volumes for checkout')
    category = models.ForeignKey(SubscriptionType, null=True, blank=True,
        help_text='Code to indicate the kind of subscription')

    # NOTE: Using decimal field to take advantage of Python's decimal handling
    # Can store up to 99999999.99 -- which is *probably* safe.
    price_paid = models.DecimalField(max_digits=10, decimal_places=2,
        blank=True, null=True)
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    SUPPLEMENT = 'sup'
    RENEWAL = 'ren'
    OTHER = 'oth'

    EVENT_TYPE_CHOICES = (
        ('', 'Subscription'),
        (SUPPLEMENT, 'Supplement'),
        (RENEWAL, 'Renewal'),
        (OTHER, 'Other'),
    )
    subtype = models.CharField(verbose_name='Type', max_length=50, blank=True,
        choices=EVENT_TYPE_CHOICES,
        help_text='Type of subscription event, e.g. supplement or renewal.')

    def save(self, *args, **kwargs):
        # recalculate duration on save if dates are available,
        # so that duration is always accurate even if dates change
        if self.start_date and self.end_date:
            self.calculate_duration()
        super(Subscription, self).save(*args, **kwargs)

    def calculate_duration(self):
        '''calculate and set subscription duration based on start and end
        date, when both are known'''
        if self.start_date and self.end_date:
            # calculate duration in days as timedelta from end to start
            self.duration = (self.end_date - self.start_date).days

    def validate_unique(self, *args, **kwargs):
        '''Validation check to prevent duplicate events from being
        added to the system.  Does not allow more than one subscription
        for the same account and date.'''
        super(Subscription, self).validate_unique(*args, **kwargs)

        # check to prevent duplicate event
        # should not have same date + account + event subtype
        # (can't use unique_together because of multi-table inheritance)

        # adapted from https://stackoverflow.com/questions/7366363/adding-custom-django-model-validation
        qs = Subscription.objects.filter(start_date=self.start_date,
            account=self.account, subtype=self.subtype)

        # if current work is already saved, exclude it from the queryset
        if not self._state.adding and self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError('Subscription event is not unique')

    def readable_duration(self):
        '''Generate a human-readable version of the subscription duration.
        Intended to follow Beach's conventions, e.g. 1 year rather than
        12 months; 1 week rather than 7 days.'''

        # simple case - days/weeks less than a month
        if self.duration and self.duration < 28:
            # weeks are sets of 7 days exactly
            if self.duration % 7 == 0:
                weeks = self.duration / 7
                return '%d week%s' % (weeks, pluralize(weeks))
            # days less than a week
            if self.duration < 7:
                return '%d day%s' % (self.duration, pluralize(self.duration))

        # otherwise, use relativedelta to generate duration in years/months/days
        # and aggregate the different units
        parts = []
        rel_dur = relativedelta(self.end_date, self.start_date)
        if rel_dur.years:
            parts.append('%d year%s' % (rel_dur.years, pluralize(rel_dur.years)))
        if rel_dur.months:
            parts.append('%d month%s' % (rel_dur.months, pluralize(rel_dur.months)))
        if rel_dur.days:
            parts.append('%d day%s' % (rel_dur.days, pluralize(rel_dur.days)))

        # if there are multiple parts (e.g., 1 month and 11 days) and
        # duration is evenly divisible by 7, display as weeks
        # NOTE: this could potentially match 1 year + some number of months;
        # unclear what behavior would be preferred in that case,
        # but unlikely to happen with current MEP data
        if len(parts) > 1 and self.duration % 7 == 0:
            weeks = self.duration / 7
            return '%d week%s' % (weeks, pluralize(weeks))

        # otherwise, combine months & days
        return ', '.join(parts)
    readable_duration.short_description = 'Duration'
    readable_duration.admin_order_field = 'duration'


class Borrow(Event):
    '''Inherited table indicating borrow events'''
    #: :class:`~mep.books.models.Work` that was borrowed;
    #: optional to account for unclear titles
    ITEM_RETURNED = 'R'
    ITEM_BOUGHT = 'B'
    ITEM_MISSING = 'M'
    STATUS_CHOICES = (
        ('', 'Unknown'),
        (ITEM_RETURNED, 'Returned'),
        (ITEM_BOUGHT, 'Bought'),
        (ITEM_MISSING, 'Missing'),
    )
    item_status = models.CharField(
        max_length=2, blank=True,
        help_text='Status of borrowed item (bought, missing, returned)',
        choices=STATUS_CHOICES)
    footnotes = GenericRelation(Footnote, related_query_name='borrows')

    def save(self, *args, **kwargs):
        # if end date is set and item status is not, automatically set
        # status to returned
        if self.end_date and not self.item_status:
            self.item_status = self.ITEM_RETURNED
        super(Borrow, self).save(*args, **kwargs)

    def status(self):
        if self.item_status == self.ITEM_RETURNED:
            return self.STATUS_CHOICES[1][1]
        elif self.item_status == self.ITEM_BOUGHT:
            return self.STATUS_CHOICES[2][1]
        elif self.item_status == self.ITEM_MISSING:
            return self.STATUS_CHOICES[3][1]
        return self.STATUS_CHOICES[0][1]


class Purchase(CurrencyMixin, Event):
    '''Inherited table indicating purchase events; extends :class:`Event`'''
    price = models.DecimalField(max_digits=8, decimal_places=2,
                                blank=True, null=True)
    footnotes = GenericRelation(Footnote, related_query_name='purchases')

    def date(self):
        '''alias of :attr:`date_range` for display; since reimbersument
        is a single-day event will always be a single partial date.'''
        return self.date_range
    date.admin_order_field = 'start_date'

    def save(self, *args, **kwargs):
        # override save to always set start = end, end will be disabled in
        # admin
        self.end_date_precision = self.start_date_precision
        self.end_date = self.start_date
        super().save(*args, **kwargs)

    def validate_unique(self, *args, **kwargs):
        '''Validation check to prevent duplicate purchase events from happening.
        Differs from
        :class:`~mep.accounts.models.Reimbursement.validate_unique` by also
        allowing for multiple purchases of different items per day. Used
        instead of `unique_together` because of multi-table inheritance.
        '''
        super().validate_unique(*args, **kwargs)
        # check to prevent duplicate event (date + account + item)
        try:
            qs = Purchase.objects.filter(start_date=self.start_date,
                account=self.account, work=self.work)
        except ObjectDoesNotExist:
            # bail out without making any further assertions because
            # we've had a missing required related field and other checks
            # will catch it
            return

        # if current work is already saved, exclude it from the queryset
        if not self._state.adding and self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError('Purchase event is not unique')


class Reimbursement(Event, CurrencyMixin):
    '''Reimbursement event; extends :class:`Event`'''
    refund = models.DecimalField(max_digits=8, decimal_places=2, null=True,
        blank=True)

    def date(self):
        '''alias of :attr:`start_date` for display, since reimbersument
        is a single-day event'''
        return self.start_date
    date.admin_order_field = 'start_date'

    def save(self, *args, **kwargs):
        '''Reimbursement is a single-day event; populate end date on save
        to make that explicit and simplify any generic event date
        range searching and filtering.'''
        self.end_date = self.start_date
        super(Reimbursement, self).save(*args, **kwargs)

    def validate_unique(self, *args, **kwargs):
        '''Validation check to prevent duplicate events from being
        added to the system.  Does not allow more than one reimbursement
        for the account and date. Used instead of
        `unique_together` because of multi-table inheritance.'''
        super(Reimbursement, self).validate_unique(*args, **kwargs)

        # check to prevent duplicate event (reimbursement + date + account)
        # should not have same date + account
        try:
            qs = Reimbursement.objects.filter(start_date=self.start_date,
                account=self.account)
        except ObjectDoesNotExist:
            # bail out without making any further assertions because
            # we've had a missing related field and other checks
            # will catch it
            return
        # if current work is already saved, exclude it from the queryset
        if not self._state.adding and self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError('Reimbursement event is not unique')
