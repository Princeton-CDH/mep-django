import datetime
import re
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models.query import QuerySet
from django.core.validators import ValidationError
from django.test import TestCase
import pytest

from mep.accounts.models import Account, Address, \
    Borrow, Event, Purchase, Reimbursement, Subscription, CurrencyMixin, \
    DatePrecisionField, DatePrecision, PartialDate, PartialDateMixin
from mep.books.models import Item
from mep.people.models import Person, Location
from mep.footnotes.models import Bibliography, SourceType


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
        loc1 = Location.objects.create(street_address='1 Rue St.')
        Address.objects.create(account=account, location=loc1)
        assert str(account) == "Account #%s: 1 Rue St." % account.pk

        # create and add a person, overrides address
        pers1 = Person.objects.create(name='Mlle Foo')
        account.persons.add(pers1)
        assert str(account) == "Account #%s: Mlle Foo" % account.pk

    def test_add_event(self):

        # Make a saved Account object
        account = Account.objects.create()
        account.add_event('reimbursement', **{'refund': 2.32})

        # Look at the relationship from the other side via Reimbursement
        # should find the event we just saved
        reimbursement = Reimbursement.objects.get(account=account)
        assert float(reimbursement.refund) == 2.32

        # Saving with a not saved object should raise ValueError
        with pytest.raises(ValueError):
            unsaved_account = Account()
            unsaved_account.add_event('reimbursement', **{'refund': 2.32})

        # Providing a dud event type should raise ValueError
        with pytest.raises(ValueError):
            account.add_event('foo')

    def test_get_events(self):
        # Make a saved Account object
        account = Account.objects.create()
        account.add_event('reimbursement', **{'refund': 2.32})
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
        assert float(reimbursements[0].refund) == 2.32

        # Try filtering so that we get no reimbursements and empty qs
        reimbursements = account.get_events('reimbursement', refund=2.45)
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

    def test_list_locations(self):
        # create an account and associate three addresses with it
        account = Account.objects.create()
        loc1 = Location.objects.create(name='Hotel Foo', city='Paris')
        loc2 = Location.objects.create(street_address='1 Foo St.', city='London')
        loc3 = Location.objects.create(city='Berlin')
        locations = [loc1, loc2, loc3]
        for location in locations:
            Address.objects.create(account=account, location=location)

        # semicolon separated string sorted by city, name, street address,
        # displays name first, then street_address, and city as a last resort
        account.list_locations() == 'Berlin; 1 Foo St.; Hotel Foo'

    def test_event_dates(self):
        account = Account.objects.create()
        # no dates, no error
        assert account.event_dates == []

        # single date
        date1 = datetime.date(1943, 1, 1)
        event1 = Subscription.objects.create(account=account, start_date=date1)
        assert account.event_dates == [date1]

        # multiple dates
        date2 = datetime.date(1945, 5, 1)
        event1.end_date = date2
        event1.save()
        date3 = datetime.date(1945, 6, 1)
        Subscription.objects.create(account=account, start_date=date3)

        # should include all dates in order
        assert account.event_dates == [date1, date2, date3]

        # duplicate dates are not repeated
        Subscription.objects.create(account=account, start_date=date2,
                                    end_date=date3)
        assert account.event_dates == [date1, date2, date3]

    def test_earliest_date(self):
        account = Account.objects.create()
        # no date, no error
        assert not account.earliest_date()

        event1 = Subscription.objects.create(account=account,
            start_date=datetime.date(1943, 1, 1),
            end_date=datetime.date(1944, 1, 1))
        event2 = Reimbursement.objects.create(account=account,
            start_date=datetime.date(1944, 5, 1))

        assert account.earliest_date() == event1.start_date

        # skip empty start date
        event1.start_date = None
        event1.save()
        assert account.earliest_date() == event1.end_date

    def test_last_date(self):
        account = Account.objects.create()
        # no date, no error
        assert not account.last_date()

        # subscription with no end date - start date should
        # be used
        event = Subscription.objects.create(
            account=account, start_date=datetime.date(1943, 1, 1))
        assert account.last_date() == event.start_date

        # multiple events; use the last
        event1 = Subscription.objects.create(
            account=account, start_date=datetime.date(1943, 1, 1),
            end_date=datetime.date(1944, 1, 1))
        event2 = Reimbursement.objects.create(
            account=account, start_date=datetime.date(1944, 5, 1))

        assert account.last_date() == event2.end_date

    def test_subscription_set(self):
        account = Account.objects.create()
        assert isinstance(account.subscription_set, QuerySet)
        assert not account.subscription_set.exists()

        # add some events
        subs = Subscription.objects.create(account=account,
            start_date=datetime.date(1943, 1, 1))
        subs2 = Subscription.objects.create(account=account,
            start_date=datetime.date(1943, 1, 1),
            end_date=datetime.date(1944, 1, 1))
        reimb = Reimbursement.objects.create(account=account,
            start_date=datetime.date(1944, 5, 1))
        generic = Event.objects.create(account=account)

        subscriptions = account.subscription_set
        assert subscriptions.count() is 2
        assert isinstance(subscriptions.first(), Subscription)
        assert subs in subscriptions
        assert subs2 in subscriptions
        assert reimb not in subscriptions
        assert generic not in subscriptions

    def test_reimbursement_set(self):
        account = Account.objects.create()
        assert isinstance(account.reimbursement_set, QuerySet)
        assert not account.reimbursement_set.exists()

        # add some events, including some that should not be in the queryset
        reimb1 = Reimbursement.objects.create(account=account,
            start_date=datetime.date(1943, 1, 1), end_date=None,
            refund=12.00)
        reimb2 = Reimbursement.objects.create(account=account,
            start_date=datetime.date(1957, 1, 1), end_date=None, refund=15.00)
        subs = Subscription.objects.create(account=account,
            start_date=datetime.date(1943, 1, 1))
        generic = Event.objects.create(account=account)
        reimbursements = account.reimbursement_set.all()

        # two reimbursements are includedm and they are the ones created
        assert reimbursements.count() == 2
        assert reimb1 in reimbursements
        assert reimb2 in reimbursements
        # a Subscription and generic Event are not
        assert subs not in reimbursements
        assert generic not in reimbursements

    def test_has_card(self):
        account = Account()
        assert not account.has_card()

        src_type = SourceType.objects.get_or_create(name='Lending Library Card')[0]
        card = Bibliography.objects.create(bibliographic_note='John\'s library card',
            source_type=src_type)
        account.card = card
        assert account.has_card()


class TestAddress(TestCase):

    def setUp(self):
        self.location = Location.objects.create(name='Hotel de la Rue')
        self.account = Account.objects.create()

        self.address = Address.objects.create(
            location=self.location,
            account=self.account
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Address \{.+\}>")
        assert re.search(overall, repr(self.address))

    def test_str(self):
        # account only
        assert str(self.address) == '%s - %s' % (self.location, self.account)

        # account with start date
        start_year = 1920
        self.address.start_date = datetime.datetime(year=start_year, month=1, day=1)
        assert str(self.address) == \
            '%s - %s (%s-)' % (self.location, self.account, start_year)

        # start and end date
        end_year = 1923
        self.address.end_date = datetime.datetime(year=end_year, month=1, day=1)
        assert str(self.address) == \
            '%s - %s (%d-%d)' % (self.location, self.account, start_year, end_year)

        # end date only
        self.address.start_date = None
        assert str(self.address) == \
            '%s - %s (-%d)' % (self.location, self.account, end_year)

        # care of person
        self.address.care_of_person = Person.objects.create(name='Jones')
        assert str(self.address) == \
            '%s - %s (-%d) c/o %s' % (self.location, self.account, end_year,
                                    self.address.care_of_person)
        # care of, no dates
        self.address.end_date = None
        assert str(self.address) == \
            '%s - %s c/o %s' % (self.location, self.account,
                                self.address.care_of_person)

        # person, no account
        self.address.account = None
        self.address.person = Person.objects.create(name='Smith')
        assert str(self.address) == \
            '%s - %s c/o %s' % (self.location, self.address.person,
                                self.address.care_of_person)

    def test_clean(self):
        addr = Address(location=self.location)
        # no account or person is an error
        with pytest.raises(ValidationError):
            addr.clean()
        addr.account = self.account
        addr.person = Person.objects.create(name='Lee')

        # both account and person is an error
        with pytest.raises(ValidationError):
            addr.clean()

        # either one alone should not raise an exception
        # - person only
        addr.account = None
        addr.clean()
        # - account only
        addr.person = None
        addr.account = self.account
        addr.clean()


class TestEvent(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.item = Item.objects.create(title='Selected poems')
        self.event = Event.objects.create(account=self.account)

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Event \{.+\}>")
        assert re.search(overall, repr(self.event))

    def test_str(self):
        assert str(self.event) == \
            'Event for account #%s ??/??' % self.account.pk

    def test_date_range(self):
        assert self.event.date_range == '??/??'

        # start only
        self.event.start_date = datetime.date(2018, 5, 1)
        assert self.event.date_range == '%s/??' % self.event.start_date.isoformat()

        # both start and end set, different values
        self.event.end_date = datetime.date(2020, 6, 11)
        assert self.event.date_range == '{}/{}'.format(self.event.start_date,
                                                       self.event.end_date)

        # both set, same values
        self.event.end_date = self.event.start_date
        assert self.event.date_range == self.event.start_date.isoformat()

        # end date only
        self.event.start_date = None
        assert self.event.date_range == '??/{}'.format(self.event.end_date.isoformat())

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
            refund=2.30,
            currency='USD'
        )
        assert reimbursement.event_ptr.event_type == 'Reimbursement'

        # borrow
        borrow = Borrow.objects.create(account=self.account, item=self.item)
        assert borrow.event_ptr.event_type == 'Borrow'

        # purchase
        purchase = Purchase.objects.create(account=self.account,
            item=self.item, price=5)
        assert purchase.event_ptr.event_type == 'Purchase'


class TestSubscription(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.subscription = Subscription.objects.create(
            account=self.account,
            start_date=datetime.date(1940, 4, 8),
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
        assert str(self.subscription) == \
            'Subscription for account #%s %s/??' % \
            (self.subscription.account.pk, self.subscription.start_date.isoformat())

    def test_validate_unique(self):
        # resaving existing record should not error
        self.subscription.validate_unique()

        # creating new subscription for same account & date should error
        with pytest.raises(ValidationError):
            subscr = Subscription(account=self.account,
                start_date=self.subscription.start_date)
            subscr.validate_unique()

        # same account + date with different subtype should be fine
        subscr = Subscription(account=self.account,
            start_date=self.subscription.start_date, subtype='ren')
        subscr.validate_unique()

    def test_calculate_duration(self):
        # create subscription with start date of today and
        # adjust end date to test duration calculations
        today = datetime.datetime.now()

        # single day
        delta = relativedelta(days=3)
        subs = Subscription(start_date=today, end_date=today + delta)
        subs.calculate_duration()
        expect = 3
        assert subs.duration == expect, \
            "%s should generate duration of '%d', got '%d'" % \
                (delta, expect, subs.duration)

        # month duration should be actual day count
        # February in a non-leap year; 28 days
        subs = Subscription(start_date=datetime.date(2017, 2, 1),
                            end_date=datetime.date(2017, 3, 1))
        subs.calculate_duration()
        expect = 28
        assert subs.duration == expect, \
            "Month of February should generate duration of '%d', got '%d'" % \
                (expect, subs.duration)
        # January in any year; 31 days
        subs = Subscription(start_date=datetime.date(2017, 1, 1),
                            end_date=datetime.date(2017, 2, 1))
        subs.calculate_duration()
        expect = 31
        assert subs.duration == expect, \
            "Month of January should generate duration of '%d', got '%d'" % \
                (expect, subs.duration)

    def test_save(self):
        acct = Account.objects.create()
        subs = Subscription(account=acct)

        # test that calculate duration is called when it should be
        with patch.object(subs, 'calculate_duration') as mock_calcdur:
            # no dates - not called
            subs.save()
            mock_calcdur.assert_not_called()

            # start date only
            subs.start_date = datetime.date.today()
            subs.save()
            mock_calcdur.assert_not_called()

            # end date only
            subs.start_date = None
            subs.end_date = datetime.date.today()
            subs.save()
            mock_calcdur.assert_not_called()

            # both start and end dates
            subs.start_date = datetime.date.today()
            subs.save()
            mock_calcdur.assert_any_call()

            # duration set - should still recalculate in case of change
            subs.duration = 250
            mock_calcdur.reset_mock()
            subs.save()
            mock_calcdur.assert_any_call()

    def test_readable_duration(self):
        # create subscription with start date of today and
        # adjust end date to test duration display
        today = datetime.datetime.now()
        acct = Account.objects.create()

        # single day
        delta = relativedelta(days=1)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '1 day'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)
        # two days
        delta = relativedelta(days=2)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '2 days'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)

        # single month
        delta = relativedelta(months=1)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '1 month'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)
        # multiple months
        delta = relativedelta(months=6)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '6 months'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)

        # single year
        delta = relativedelta(years=1)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '1 year'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)
        # multiple years
        delta = relativedelta(years=2)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '2 years'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)

        # one week
        delta = relativedelta(days=7)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '1 week'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)
        # two weeks
        delta = relativedelta(days=7 * 2)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '2 weeks'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)
        # six weeks
        delta = relativedelta(days=7 * 6)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '6 weeks'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)

        # combined units
        delta = relativedelta(years=1, days=3)
        subs = Subscription.objects.create(account=acct,
            start_date=today, end_date=today + delta)
        dur = subs.readable_duration()
        expect = '1 year, 3 days'
        assert dur == expect, \
            "%s should display as '%s', got '%s'" % (delta, expect, dur)

        # special cases
        # test February in a non-leap year; 28 days, should display as one month
        subs = Subscription.objects.create(account=acct,
            start_date=datetime.date(2017, 2, 1), end_date=datetime.date(2017, 3, 1))
        dur = subs.readable_duration()
        expect = '1 month'
        assert dur == expect, \
            "Month of February should display as '%s', got '%s'" % (expect, dur)


class TestPurchase(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.purchase = Purchase(
            account=self.account,
            price=2.30,
            currency='USD',
            item=Item.objects.create(title='Le Foo'),
        )
        self.purchase.calculate_date('start_date', '1920-02-03')
        self.purchase.save()

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Purchase \{.+\}>")
        assert re.search(overall, repr(self.purchase))

    def test_str(self):
        assert str(self.purchase) == ('Purchase for account #%s 1920-02-03' %
                                      self.purchase.account.pk)

    def test_save(self):
        # no end date or precision
        self.purchase.end_date = None
        self.purchase.end_date_precision = None
        self.purchase.save()
        # save should set end_date and end_date_precision
        assert self.purchase.end_date == self.purchase.start_date
        assert self.purchase.end_date_precision == self.purchase.start_date_precision

    def test_validate_unique(self):
        # resaving existing record should not error
        self.purchase.validate_unique()

        # creating new purchase for same account, date, and item should error
        with pytest.raises(ValidationError):
            purchase = Purchase(
                account=self.account,
                start_date=self.purchase.start_date,
                item=self.purchase.item,
                price=self.purchase.price
            )
            purchase.validate_unique()

        # a new purchase on same date and account, but different item,
        # should not trigger ValidationError
        purchase = Purchase(
            account=self.account,
            start_date=self.purchase.start_date,
            item=Item.objects.create(title='Le Bar'),
            price=self.purchase.price
        )
        purchase.validate_unique()

        # not setting an account should not raise an error (caught by other
        # checks)
        Purchase().validate_unique()


class TestReimbursement(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.reimbursement = Reimbursement.objects.create(
            account=self.account,
            refund=2.30,
            currency='USD',
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Reimbursement \{.+\}>")
        assert re.search(overall, repr(self.reimbursement))

    def test_str(self):
        assert str(self.reimbursement) == ('Reimbursement for account #%s ??/??' %
                                           self.reimbursement.account.pk)

    def test_validate_unique(self):
        # resaving existing record should not error
        self.reimbursement.validate_unique()

        # creating new reimbursement for same account & date should error
        with pytest.raises(ValidationError):
            reimburse = Reimbursement(account=self.account,
                start_date=self.reimbursement.start_date)
            reimburse.validate_unique()

        # a new reimbursement that is not on the same date should not be caught
        reimburse = Reimbursement(account=self.account,
            start_date=datetime.date(1919, 1, 1))
        reimburse.validate_unique()

        # a reimbursement withment without an account should not raise
        # a related object error
        Reimbursement().validate_unique()


    def test_auto_end_date(self):
        self.reimbursement.start_date = datetime.datetime.now()
        self.reimbursement.save()
        assert self.reimbursement.end_date == self.reimbursement.end_date

        self.reimbursement.start_date = None
        self.reimbursement.save()
        assert not self.reimbursement.end_date


class TestBorrow(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.item = Item.objects.create(title='Collected works')
        self.borrow = Borrow.objects.create(
            account=self.account, item=self.item
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Borrow \{.+\}>")
        assert re.search(overall, repr(self.borrow))

    def test_str(self):
        assert str(self.borrow) == ('Borrow for account #%s ??/??' %
                                    self.borrow.account.pk)

        start_date = datetime.date(2018, 5, 1)
        self.borrow.partial_start_date = start_date.isoformat()
        assert str(self.borrow).endswith('%s/??' % start_date.isoformat())

        # handle partial dates
        self.borrow.partial_start_date = '2018-05'
        print(self.borrow)
        assert str(self.borrow).endswith('%s/??' % self.borrow.partial_start_date)

    def test_save(self):
        today = datetime.date.today()
        borrow = Borrow(account=self.account, item=self.item)
        # no end date, no item status; item status should not be set
        borrow.save()
        assert not borrow.item_status
        # end date, status - item status should automatically be set
        borrow.end_date = today
        borrow.save()
        assert borrow.item_status == borrow.ITEM_RETURNED
        # if status set, it should not be changed
        borrow.item_status = borrow.ITEM_MISSING
        borrow.save()
        assert borrow.item_status == borrow.ITEM_MISSING


class TestPartialDateMixin(TestCase):

    class PartialMixinObject(PartialDateMixin):

        class Meta:
            abstract = True

    def test_calculate_date(self):

        pmo = self.PartialMixinObject()
        with pytest.raises(ValueError):
            # unsupported date name should error
            pmo.calculate_date('bogus')

        # partial date
        pmo.calculate_date('start_date', '1935-05')
        assert pmo.start_date == datetime.date(1935, 5, 1)
        assert pmo.start_date_precision.year
        assert pmo.start_date_precision.month
        assert not pmo.start_date_precision.day

        # 1900 date = unknown by project convention
        pmo.calculate_date('end_date', '1901-06-30')
        assert pmo.end_date == datetime.date(1901, 6, 30)
        assert not pmo.end_date_precision.year
        assert pmo.end_date_precision.month
        assert pmo.end_date_precision.day

        # earliest/latest dates
        early = datetime.date(1930, 11, 5)
        late = datetime.date(1930, 11, 25)
        pmo.calculate_date('start_date', earliest=early, latest=late)
        # stored as earliest date
        assert pmo.start_date == early
        assert pmo.partial_start_date == '1930-11'
        # in this case, all but day match
        assert pmo.start_date_precision.year
        assert pmo.start_date_precision.month
        assert not pmo.start_date_precision.day

        # only year overlaps
        late = datetime.date(1930, 12, 25)
        pmo.calculate_date('start_date', earliest=early, latest=late)
        assert pmo.partial_start_date == '1930'
        assert pmo.start_date_precision.year
        assert not pmo.start_date_precision.month

        # different year but same month/day
        late = datetime.date(1932, 11, 5)
        pmo.calculate_date('start_date', earliest=early, latest=late)
        assert pmo.start_date == early
        assert pmo.partial_start_date == '--11-05'
        assert not pmo.start_date_precision.year
        assert pmo.start_date_precision.month
        assert pmo.start_date_precision.day

        # no overlap?
        late = datetime.date(1932, 12, 22)
        pmo.calculate_date('start_date', earliest=early, latest=late)
        assert not pmo.partial_start_date
        assert not pmo.start_date_precision

    def test_date_range(self):

        # test both dates being the same returning date in partial date format
        pmo = self.PartialMixinObject()
        pmo.calculate_date('start_date', '1930-01-01')
        pmo.calculate_date('end_date', '1930-01-01')
        assert pmo.date_range == '1930-01-01'

        # test that two dates produce / joined dates
        pmo.calculate_date('end_date', '1930-01-02')
        assert pmo.date_range == '1930-01-01/1930-01-02'

        # test that an unknown date is rendered as ??
        pmo.end_date = None
        pmo.calculate_date('end_date')
        assert pmo.date_range == '1930-01-01/??'


class TestCurrencyMixin(TestCase):

    # create test currency model to test mixin behavior
    class CurrencyObject(CurrencyMixin):

        class Meta:
            abstract = True

    def test_currency_symbol(self):
        coin = self.CurrencyObject()
        # default value is Franc
        assert coin.currency_symbol() == '₣'

        coin.currency = CurrencyMixin.USD
        assert coin.currency_symbol() == '$'

        coin.currency = CurrencyMixin.GBP
        assert coin.currency_symbol() == '£'

        coin.currency = ''
        assert coin.currency_symbol() == ''

        # not a valid choice, but test fallback display behavior
        # when symbol is not known
        coin.currency = 'foo'
        assert coin.currency_symbol() == 'foo'


class TestPartialDates(TestCase):

    # test object for partial date descriptor behavior
    class PartialDateObject(models.Model):
        date = None
        partial_date = PartialDate('date', 'date_precision')
        date_precision = DatePrecisionField()

        class Meta:
            abstract = True

    # version that uses 1900 for unknown years
    class PartialDateObject1900(PartialDateObject):
        partial_date = PartialDate('date', 'date_precision', 1900)

        class Meta:
            abstract = True

    def test_get(self):
        pdo = self.PartialDateObject()
        # should not error if date is not set
        assert pdo.partial_date is None
        # full precision
        pdo.date = datetime.date(1901, 3, 5)
        pdo.date_precision = DatePrecision.year | DatePrecision.month | DatePrecision.day
        assert pdo.partial_date == '1901-03-05'
        # partial precision
        pdo.date_precision = DatePrecision.year | DatePrecision.month
        assert pdo.partial_date == '1901-03'
        pdo.date_precision = DatePrecision.month | DatePrecision.day
        assert pdo.partial_date == '--03-05'
        pdo.date_precision = DatePrecision.year
        assert pdo.partial_date == '1901'
        # change default unknown year value
        pdo = self.PartialDateObject1900()
        pdo.date = datetime.date(1900, 3, 5)
        pdo.date_precision = DatePrecision.month | DatePrecision.day
        assert pdo.partial_date == '--03-05'

    def test_set(self):
        pdo = self.PartialDateObject()
        # full precision
        pdo.partial_date = '1901-03-05'
        assert pdo.date == datetime.date(1901, 3, 5)
        assert pdo.date_precision == DatePrecision.year | DatePrecision.month | DatePrecision.day
        # partial precision
        pdo.partial_date = '1901-03'
        assert pdo.date == datetime.date(1901, 3, 1)
        assert pdo.date_precision == DatePrecision.year | DatePrecision.month
        pdo.partial_date = '--03-05'
        assert pdo.date == datetime.date(1, 3, 5)
        assert pdo.date_precision == DatePrecision.month | DatePrecision.day
        pdo.partial_date = '1901'
        assert pdo.date == datetime.date(1901, 1, 1)
        assert pdo.date_precision == DatePrecision.year
        # invalid partial precision
        with pytest.raises(ValidationError):
            pdo.partial_date = '05'
        with pytest.raises(ValidationError):
            pdo.partial_date = '1901--05'
        with pytest.raises(ValidationError):
            pdo.partial_date = 'definitely_not_a_date'
        # should clear the values if None is passed
        pdo.partial_date = None
        assert pdo.date is None
        assert pdo.date_precision is None
        # change default unknown year value
        pdo = self.PartialDateObject1900()
        pdo.partial_date = '--03-05'
        assert pdo.date == datetime.date(1900, 3, 5)
        assert pdo.date_precision == DatePrecision.month | DatePrecision.day
