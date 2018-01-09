import pytest
import re

from django.test import TestCase
from mep.accounts.models import Account, AccountAddress, Address
from mep.accounts.models import Borrow, Event, Purchase, Reimbursement, \
    Subscription
from mep.books.models import Item
from mep.people.models import Address, Person


class TestAccount(TestCase):

    def test_repr(self):
        account = Account()
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>""
        overall = re.compile(r"<Account \{.+\}>")
        assert re.search(overall, repr(account))

    def test_str(self):
        # create and save an account
        account = Account.objects.create()
        assert str(account) == "Account #%s" % account.pk

        # create and add an address, overrides just pk method
        add1 = Address.objects.create(street_address='1 Rue St.')
        AccountAddress.objects.create(account=account, address=add1)
        assert str(account) == "Account #%s: 1 Rue St." % account.pk

        # create and add a person, overrides address
        pers1 = Person.objects.create(name='Mlle Foo')
        account.persons.add(pers1)
        assert str(account) == "Account #%s: Mlle Foo" % account.pk

    def test_add_event(self):

        # Make a saved Account object
        account = Account.objects.create()
        account.add_event('reimbursement', **{'price': 2.32})

        # Look at the relationship from the other side via Reimbursement
        # should find the event we just saved
        reimbursement = Reimbursement.objects.get(account=account)
        assert float(reimbursement.price) == 2.32

        # Saving with a not saved object should raise ValueError
        with pytest.raises(ValueError):
            unsaved_account = Account()
            unsaved_account.add_event('reimbursement', **{'price': 2.32})

        # Providing a dud event type should raise ValueError
        with pytest.raises(ValueError):
            account.add_event('foo')

    def test_get_events(self):
        # Make a saved Account object
        account = Account.objects.create()
        account.add_event('reimbursement', **{'price': 2.32})
        account.add_event(
            'subscription',
            **{'duration': 1, 'volumes': 2, 'price_paid': 4.56}
        )

        # Access them as events only
        assert len(account.get_events()) == 2
        assert isinstance(account.get_events()[0], Event)

        # Now access as a subclass with related properties
        reimbursements = account.get_events('reimbursement')
        assert len(reimbursements) == 1
        assert float(reimbursements[0].price) == 2.32

        # Try filtering so that we get no reimbursements and empty qs
        reimbursements = account.get_events('reimbursement', price=2.45)
        assert not reimbursements

        # Providing a dud event type should raise ValueError
        with pytest.raises(ValueError):
            account.add_event('foo')

    def test_list_persons(self):
        # create an account and associate two people with it
        account = Account.objects.create()
        pers1 = Person.objects.create(name='Foobar')
        pers2 = Person.objects.create(name='Bazbar')
        account.persons.add(pers1, pers2)

        # comma separated string, by name in alphabetical order
        assert account.list_persons() == 'Bazbar, Foobar'

    def test_list_addresses(self):
        # create an account and associate three addresses with it
        account = Account.objects.create()
        add1 = Address.objects.create(name='Hotel Foo', city='Paris')
        add2 = Address.objects.create(street_address='1 Foo St.', city='London')
        add3 = Address.objects.create(city='Berlin')
        addresses = [add1, add2, add3]
        for address in addresses:
            AccountAddress.objects.create(account=account, address=address)

        # semicolon separated string sorted by city, name, street address,
        # displays name first, then street_address, and city as a last resort
        account.list_addresses() == 'Berlin; 1 Foo St.; Hotel Foo'


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


class TestEvent(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.event = Event.objects.create(account=self.account)

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Event \{.+\}>")
        assert re.search(overall, repr(self.event))

    def test_str(self):
        assert str(self.event) == 'Event for account #%s' % self.account.pk

    def test_event_type(self):
        assert self.event.event_type == 'Generic'
        # Create a subscription and check its generic event type
        subscription = Subscription.objects.create(
                account=self.account,
                duration=1,
                volumes=2,
                price_paid=3.20
        )
        # subscriptio, not otherwise specified
        assert subscription.event_ptr.event_type == 'Subscription'
        # subscription labeled as a supplement
        subscription.subtype = Subscription.SUPPLEMENT
        subscription.save()
        assert subscription.event_ptr.event_type == 'Supplement'
        # subscription labeled as a renewal
        subscription.subtype = Subscription.RENEWAL
        subscription.save()
        assert subscription.event_ptr.event_type == 'Renewal'

        # Create a reimbursement check its event type
        reimbursement = Reimbursement.objects.create(
            account=self.account,
            price=2.30,
            currency='USD'
        )
        assert reimbursement.event_ptr.event_type == 'Reimbursement'

class TestSubscription(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.subscription = Subscription.objects.create(
            account=self.account,
            duration=1,
            volumes=2,
            price_paid=3.20
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Subscription \{.+\}>")
        assert re.search(overall, repr(self.subscription))

    def test_str(self):
        assert str(self.subscription) == ('Subscription for account #%s' %
                                       self.subscription.account.pk)


class TestPurchase(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.item = Item.objects.create(
            title='Foobar'
        )
        self.purchase = Purchase.objects.create(
            account=self.account,
            price=2.30,
            currency='USD',
            item=self.item,
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Purchase \{.+\}>")
        assert re.search(overall, repr(self.purchase))

    def test_str(self):
        assert str(self.purchase) == ('Purchase for account #%s' %
                                      self.purchase.account.pk)


class TestReimbursement(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.reimbursement = Reimbursement.objects.create(
            account=self.account,
            price=2.30,
            currency='USD'
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Reimbursement \{.+\}>")
        assert re.search(overall, repr(self.reimbursement))

    def test_str(self):
        assert str(self.reimbursement) == ('Reimbursement for account #%s' %
                                           self.reimbursement.account.pk)


class TestBorrow(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.borrow = Borrow.objects.create(
            account=self.account
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Borrow \{.+\}>")
        assert re.search(overall, repr(self.borrow))

    def test_str(self):
        assert str(self.borrow) == ('Borrow for account #%s' %
                                    self.borrow.account.pk)
