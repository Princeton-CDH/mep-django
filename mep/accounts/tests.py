import pytest
import re

from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import Account, AccountAddress, Address


class TestAccount(TestCase):

    def test_repr(self):
        account = Account()
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>""
        overall = re.compile(r"<Account \{.+\}>")
        assert re.search(overall, repr(account))

    def test_str(self):
        account = Account()
        assert str(account) == "Account #%s" % account.pk


class TestAddress(TestCase):

    def test_str(self):
        # Just an address
        address = Address(address_line_1="1 Rue Le Foo")
        assert str(address) == "1 Rue Le Foo"

        # Just now with a city
        address.city_town = "Paris"
        assert str(address) == "1 Rue Le Foo, Paris"

        # With nothing
        address = Address()
        assert str(address) == "Address, no street or city given"

    def test_latlon_validate(self):
        # Valid, should pass clean fields
        address = Address(latitude=180, longitude=-180)
        address.clean_fields()

        # Not valid, should error out
        with pytest.raises(ValidationError) as err:
            address.latitude = -500
            address.clean_fields()
        assert "Lat/Lon must be between -180 and 180 degrees." in str(err)


class TestAccountAddress(TestCase):

    def setUp(self):
        self.address = Address.objects.create()
        self.account = Account.objects.create()

        self.account_address = AccountAddress.objects.create(
            address=self.address,
            account=self.account
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<AccountAddress \{.+\}>")
        assert re.search(overall, repr(self.account_address))

    def test_str(self):
        assert str(self.account_address) == (
            'Account #%s - Address #%s' %
            (self.account.pk, self.address.pk)
        )
