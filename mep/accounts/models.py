# -*- coding: utf-8 -*-
import re
import datetime

from cached_property import cached_property
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import ValidationError
from django.db import models
from django.template.defaultfilters import pluralize
from flags import Flags

from mep.books.models import Item
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
        limit_choices_to={'source_type__name': 'Lending Library Card'})

    def __repr__(self):
        return '<Account %s>' % self.__dict__

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

    def earliest_date(self):
        '''Earliest known date from all events associated with this account'''
        evt = self.event_set.order_by('start_date').first()
        if evt:
            return evt.start_date

    def last_date(self):
        '''Last known date from all events associated with this account'''

        # sort by end date then start date; if end dates are missing this
        # may not be quite right...
        evt = self.event_set.order_by('end_date', 'start_date').last()
        if evt:
            # if no end date is present, return start date
            return evt.end_date or evt.start_date

    @property
    def subscription_set(self):
        '''associated subscription events, as queryset of :class:`Subscription`'''
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
        # Catch an invalid class of event or subevent
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscription',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscription, or reimbursement')

        str_to_model = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscription': Subscription
        }
        str_to_model[etype].objects.create(account=self, **kwargs)

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
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscription',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscription, or reimbursement')

        str_to_model = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscription': Subscription
        }

        if not kwargs:
            return str_to_model[etype].objects.filter(account=self)

        return str_to_model[etype].objects.filter(account=self, **kwargs)


class Address(Notable):
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
        return '<Address %s>' % self.__dict__

    def __str__(self):
        dates = care_of = ''
        if self.start_date or self.end_date:
            dates = ' (%s)' % '-'.join([date.strftime('%Y') if date else ''
                for date in [self.start_date, self.end_date]])
        if self.care_of_person:
            care_of = ' c/o %s' % self.care_of_person

        # NOTE: this is potentially redundant if account has only a
        # location and not a name
        return '%s - %s%s%s' % (self.location, self.account or self.person,
            dates, care_of)

    def clean(self):
        '''Validate to require one and only one of :class:`Account` or
        :class:`~mep.people.models.Person`'''
        if not self.account and not self.person:
            raise ValidationError('Address must be associated with an account or person')
        if self.account and self.person:
            raise ValidationError('Address must only be associated with one of account or person')


class Event(Notable):
    '''Base table for events in the Shakespeare and Co. Lending Library'''
    account = models.ForeignKey(Account)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        # NOTE: ordering events by account person seems to be very slow
        # disabling for now
        # ordering = ('start_date', 'account__persons__sort_name')
        ordering = ('start_date', )

    # These provide generic string representation for the Event class
    # and its subclasses
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.__dict__)

    def __str__(self):
        return '%s Event for account #%s %s/%s' % \
            (self.event_type, self.account.pk, self.start_date, self.end_date)

    @cached_property
    def event_type(self):
        try:
            return self.subscription.get_subtype_display()
        except ObjectDoesNotExist:
            pass
        try:
            self.reimbursement
            return 'Reimbursement'
        except ObjectDoesNotExist:
            pass
        try:
            self.borrow
            return 'Borrow'
        except ObjectDoesNotExist:
            pass
        try:
            self.purchase
            return 'Purchase'
        except ObjectDoesNotExist:
            pass
        return 'Generic'


class SubscriptionType(Named, Notable):
    '''Type of subscription'''
    pass


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

        # if current item is already saved, exclude it from the queryset
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


class DatePrecision(Flags):
    '''Flag class to indicate which parts of a date are known.'''
    year = ()
    month = ()
    day = ()


class DatePrecisionField(models.PositiveSmallIntegerField):
    '''Integer representation of a :class:`DatePrecision`.'''
    description = 'Integer representation of DatePrecision flags.'

    def to_python(self, value):
        return DatePrecision(value) if value else None


class PartialDate(object):
    '''Descriptor that gets and sets a related :class:`datetime.date` and
    :class:`DatePrecision` from partial date strings, e.g. --05-02.'''

    description = 'Partial date generated from date and date precision flags'

    partial_date_re = re.compile(
       r'^(?P<year>\d{4}|-)?(?:-(?P<month>[01]\d))?(?:-(?P<day>[0-3]\d))?$'
    )

    def __init__(self, date_field, date_precision_field, unknown_year:int=1,
                 label=None):
        self.date_field = date_field
        self.date_precision_field = date_precision_field
        self.unknown_year = unknown_year

        # set attributes for display/sort in django admin
        self.admin_order_field = date_field
        if label:
            self.short_description = label

    def __get__(self, obj, objtype=None):
        '''Use :meth:`date_format` to transform a  :class:`datetime.date` and
        :class:`DatePrecision` to a partial date string. If the date doesn't
        exist yet, return None.'''
        if obj is None:
            return self
        date_val = getattr(obj, self.date_field, None)
        if date_val:
            date_precision_val = getattr(obj, self.date_precision_field)
            return date_val.strftime(self.date_format(date_precision_val))

    def __set__(self, obj, val):
        '''Call :meth:`parse_date` to parse a partial date and set the
        :class:`datetime.date` and :class:`DatePrecision`. If a falsy value was
        passed, set them both to None.'''
        (date_val, date_precision_val) = self.parse_date(val) if val else (None, None)
        setattr(obj, self.date_field, date_val)
        setattr(obj, self.date_precision_field, date_precision_val)

    @staticmethod
    def date_format(value):
        '''Return a format string for use with :meth:`datetime.date.strftime`
        to output a date with the appropriate precision'''
        parts = []
        # cast integer to date precision to check flags
        value = DatePrecision(value)

        # no precision = no date
        if not value:
            return ''

        if value.year:
            parts.append('%Y')
        else:
            # if no year, indicate with --
            parts.append('-')
        if value.month:
            parts.append('%m')
        if value.day:
            parts.append('%d')

        # this is potentially ambiguous in some cases, but those cases
        # may not be meaningful anyway
        return '-'.join(parts)

    def parse_date(self, value):
        '''Parse a partial date string and return a :class:`datetime.date`
        and precision value.'''
        # partial date parsing adapted in part from django_partial_date
        # https://github.com/ktowen/django_partial_date
        match = self.partial_date_re.match(value)
        if match:
            match_info = match.groupdict()

            # turn matched values into numbers for initializing date object
            date_values = {}
            date_parts = []
            for k, v in match_info.items():
                try:
                    date_values[k] = int(v)
                    date_parts.append(k)
                except (TypeError, ValueError): # value was None or '-'
                    date_values[k] = self.unknown_year if k == 'year' else 1

            if date_parts == ['day'] or date_parts == ['month'] or date_parts == ['year', 'day']:
                raise ValidationError('"%s" is not a recognized date.''' % value)

            # determine known date parts based on regex match values
            # and initialize pecision flags accordingly
            precision = DatePrecision.from_simple_str('|'.join(date_parts))
            return (datetime.date(**date_values), precision)

        else:
            raise ValidationError('"%s" is not a recognized date.''' % value)


class Borrow(Event):
    '''Inherited table indicating borrow events'''
    #: :class:`~mep.books.models.Item` that was borrowed;
    #: optional to account for unclear titles
    item = models.ForeignKey(Item, null=True, blank=True)
    ITEM_RETURNED = 'R'
    ITEM_BOUGHT = 'B'
    ITEM_MISSING = 'M'
    STATUS_CHOICES = (
        ('', 'Unknown'),
        (ITEM_RETURNED, 'Returned'),
        (ITEM_BOUGHT, 'Bought'),
        (ITEM_MISSING, 'Missing'),
    )
    item_status = models.CharField(max_length=2, blank=True,
        help_text='Status of borrowed item (bought, missing, returned)',
        choices=STATUS_CHOICES)
    start_date_precision = DatePrecisionField(null=True, blank=True)
    end_date_precision = DatePrecisionField(null=True, blank=True)
    UNKNOWN_YEAR = 1900
    partial_start_date = PartialDate('start_date', 'start_date_precision',
        UNKNOWN_YEAR, label='start date')
    partial_end_date = PartialDate('end_date', 'end_date_precision',
        UNKNOWN_YEAR, label='end date')

    footnotes = GenericRelation(Footnote)

    def save(self, *args, **kwargs):
        # if end date is set and item status is not, automatically set
        # status to returned
        if self.end_date and not self.item_status:
            self.item_status = self.ITEM_RETURNED
        super(Borrow, self).save(*args, **kwargs)

    def calculate_date(self, kind, dateval=None, earliest=None, latest=None):
        '''Calculate end or start date based on a single value in a
        supported partial date form or based on earliest/latest datetime.'''

        # kind must be either start_date or end_date
        if kind not in ['start_date', 'end_date']:
            raise ValueError

        # if there is a single date value, use partial date to parse it
        # and set date precision
        if dateval:
            setattr(self, 'partial_%s' % kind, dateval)
            # special case:
            # 1900 dates were used to indicate unknown year; book store didn't
            # open until 1919, so any year before that should be marked unknown
            if getattr(self, kind).year < 1919:
                setattr(self, '%s_precision' % kind,
                        DatePrecision.month | DatePrecision.day)

        # no exact date, but earliest/latest possible dates
        elif earliest and latest:
            # store earliest datetime
            setattr(self, kind, earliest)
            precision = DatePrecision()
            # calculate the precision based on values in common
            if earliest.year == latest.year:
                precision |= DatePrecision.year
            if earliest.month == latest.month:
                precision |= DatePrecision.month
            if earliest.day == latest.day:
                precision |= DatePrecision.day

            # store the precision
            setattr(self, '%s_precision' % kind, precision)


class Purchase(Event, CurrencyMixin):
    '''Inherited table indicating purchase events'''
    price = models.DecimalField(max_digits=8, decimal_places=2)
    item = models.ForeignKey(Item)


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
        for the account and date.'''
        super(Reimbursement, self).validate_unique(*args, **kwargs)

        # check to prevent duplicate event (reimbursement + date + account)
        # should not have same date + account
        qs = Reimbursement.objects.filter(start_date=self.start_date,
            account=self.account)

        # if current item is already saved, exclude it from the queryset
        if not self._state.adding and self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError('Reimbursement event is not unique')
