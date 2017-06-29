from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from mep.common.models import Notable


def verify_latlon(value):
    if not -180 <= value <= 180:
        raise ValidationError('Lat/Lon must be between -180 and 180 degrees.')


class Account(models.Model):
    '''Central model for all account and related information, M2M explicity to
    ``people.Person``'''

    persons = models.ManyToManyField('people.Person', blank=True)
    addresses = models.ManyToManyField(
        'Address',
        through='AccountAddress',
        blank=True
    )

    def __repr__(self):
        return '<Account %s>' % self.__dict__

    def __str__(self):
        # QUESTION: Better way to do this for str? Can't count on any fields.
        return 'Account #%s' % self.pk

    def add_event(self, etype='event', **kwargs):
        '''Helper function to add an ``Event`` or subclass to an ``Account`` object.
           Requires that the ``Account`` object be saved first (so it has a
           set primary key). This provides functionality normally in the
           ``self.*_set`` functionality, but not provided with subclassed
           table inheritence.

           etype - one of ``borrow``, ``event``, ``subscribe``,
           ``purchase``, ``reimbursement``
        '''
        # Catch an invalid class of event or subevent
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscribe',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscribe, or reimbursement')

        str_to_model = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscribe': Subscribe
        }
        str_to_model[etype].objects.create(account=self, **kwargs)

    def get_events(self, etype='event', **kwargs):
        '''Helper function to retrieve related events of any valid type for
        ``self.add_event()``. This provides functionality normally in the
        ``self.*_set`` functionality, but not provided with subclassed
        table inheritence.
        etype - one of ``borrow``, ``event``, ``subscribe``,
        ``purchase``, ``reimbursement``
        kwargs - if none, _set.all(), otherwise _set.filter(**kwargs)
        '''
        # Catch an invalid class of event or subevent
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscribe',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscribe, or reimbursement')

        str_to_model = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscribe': Subscribe
        }

        if not kwargs:
            return str_to_model[etype].objects.filter(account=self)

        return str_to_model[etype].objects.filter(account=self, **kwargs)



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
    country = models.ForeignKey('people.Country', blank=True, null=True)

    def __repr__(self):
        return '<Address %s>' % self.__dict__

    def __str__(self):
        if self.address_line_1 or self.city_town:
            return('%s, %s' %
                   (self.address_line_1, self.city_town)).strip(', ')
        else:
            return('Address, no street or city given')


class AccountAddress(Notable):
    '''Addresses associated with an account and optional information'''
    care_of_person = models.ForeignKey('people.Person', blank=True, null=True)
    account = models.ForeignKey('Account')
    address = models.ForeignKey('Address')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __repr__(self):
        return '<AccountAddress %s>' % self.__dict__

    def __str__(self):
        '''This is a through model, so the str representation is minimal'''
        return 'Account #%s - Address #%s' % (self.account.pk, self.address.pk)


class Event(Notable):
    '''Base table for events in the Shakespeare and Co. Lending Library'''
    account = models.ForeignKey('Account')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # These provide generic string representation for the Event class
    # and its subclasses
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.__dict__)

    def __str__(self):
        return '%s for account #%s' % (self.__class__.__name__,
                                       self.account.pk)


USD = 'USD'
FRF = 'FRF'
GBP = 'GBP'
# NOTE: Tentative set for testing
CURRENCY_CHOICES = (
    ('', '----'),
    (USD, 'US Dollar'),
    (FRF, 'French Franc'),
    (GBP, 'British Pound')
)


class Subscribe(Event):
    # QUESTION: How big does this need to be? PositiveSmallIntegerField
    # is probably appropriate.
    duration = models.PositiveSmallIntegerField()
    volumes = models.PositiveIntegerField()
    sub_type = models.CharField(max_length=255, verbose_name='type')
    # NOTE: Using decimal field to take advantage of Python's decimal handling
    # Can store up to 99999999.99 -- which is *probably* safe.
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    currency = models.CharField(max_length=3, blank=True)
    # NOTE: What are some good test types?
    FOO = 'f'
    BAR = 'b'
    MODIFICATION_CHOICES = (
        ('', '----'),
        (FOO, 'Foo'),
        (BAR, 'Bar'),
    )
    modification = models.CharField(
        max_length=50,
        blank=True,
        choices=MODIFICATION_CHOICES
    )


class Borrow(Event):
    '''Inherited table indicating borrow events'''
    # NOTE: Renamed to avoid field conflict with the table inheritences
    # The related_name should keep related queries consistently framed
    purchase_id = models.ForeignKey(
        'Purchase',
        blank=True,
        null=True,
        verbose_name='purchase',
        related_name='purchase'
    )


class Purchase(Event):
    '''Inherited table indicating purchases and linking to borrow'''
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        blank=True,
        choices=CURRENCY_CHOICES
    )


class Reimbursement(Event):
    '''Inherited table indicating purchases and linking to borrow'''
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        blank=True,
        choices=CURRENCY_CHOICES
    )
