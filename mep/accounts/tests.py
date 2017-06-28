import re

from django.test import TestCase
from .models import Account, Address


class TestAccount(TestCase):

    def test_repr(self):
        account = Account()
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {'k':v, ...}>""
        overall = re.compile(r'<Account \{.+\}>')
        assert re.search(overall, repr(account))

    def test_str(self):
        account = Account()
        assert str(account) == 'Account #%s' % account.pk


class TestAddress(TestCase):

    def test_str(self):
        # Just an address
        address = Address(address_line_1='1 Rue Le Foo')
        assert str(address) == '1 Rue Le Foo'

        # Just now with a city
        address.city_town = 'Paris'
        assert str(address) == '1 Rue Le Foo, Paris'
