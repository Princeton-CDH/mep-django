from django.core.exceptions import ValidationError
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
