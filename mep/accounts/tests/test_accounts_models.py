import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.core.validators import ValidationError
from django.db.models.query import EmptyQuerySet, QuerySet
from django.test import TestCase
from djiffy.models import Canvas, Manifest
import pytest

from mep.accounts.models import (
    Account,
    Address,
    Borrow,
    CurrencyMixin,
    Event,
    Purchase,
    Reimbursement,
    Subscription,
)
from mep.books.models import Work
from mep.footnotes.models import Bibliography, Footnote, SourceType
from mep.people.models import Location, Person


class TestAccount(TestCase):
    def test_repr(self):
        account = Account()
        # unsaved
        assert repr(account) == "<Account pk:??>"
        # saved but no names
        account.save()
        assert repr(account) == "<Account pk:%s>" % account.pk
        # one name
        pers1 = Person.objects.create(name="Mlle Foo", slug="foo")
        account.persons.add(pers1)
        assert repr(account) == "<Account pk:%s %s>" % (account.pk, str(pers1))
        # multiple names
        pers2 = Person.objects.create(name="Bazbar", slug="bazbar")
        account.persons.add(pers2)
        assert repr(account) == "<Account pk:%s %s;%s>" % (
            account.pk,
            str(pers1),
            str(pers2),
        )

    def test_str(self):
        # create and save an account
        account = Account.objects.create()
        assert str(account) == "Account #%s" % account.pk

        # create and add an address, overrides just pk method
        loc1 = Location.objects.create(street_address="1 Rue St.")
        Address.objects.create(account=account, location=loc1)
        assert str(account) == "Account #%s: 1 Rue St." % account.pk

        # create and add a person, overrides address
        pers1 = Person.objects.create(name="Mlle Foo", slug="foo")
        account.persons.add(pers1)
        assert str(account) == "Account #%s: Mlle Foo" % account.pk

    def test_validate_etype(self):
        account = Account()
        # no error
        account.validate_etype("Borrow")
        with pytest.raises(ValueError):
            account.validate_etype("Rental")

    def test_str_to_model(self):
        account = Account()
        # check that the function properly maps
        assert account.str_to_model("borrow") == Borrow
        assert account.str_to_model("purchase") == Purchase

    def test_add_event(self):
        # Make a saved Account object
        account = Account.objects.create()
        account.add_event("reimbursement", **{"refund": 2.32})

        # Look at the relationship from the other side via Reimbursement
        # should find the event we just saved
        reimbursement = Reimbursement.objects.get(account=account)
        assert float(reimbursement.refund) == 2.32

        # Saving with a not saved object should raise ValueError
        with pytest.raises(ValueError):
            unsaved_account = Account()
            unsaved_account.add_event("reimbursement", **{"refund": 2.32})

        # Providing a dud event type should raise ValueError
        with pytest.raises(ValueError):
            account.add_event("foo")

    def test_get_events(self):
        # Make a saved Account object
        account = Account.objects.create()
        account.add_event("reimbursement", **{"refund": 2.32})
        account.add_event(
            "subscription", **{"duration": 1, "volumes": 2, "price_paid": 4.56}
        )

        # Access them as events only
        assert len(account.get_events()) == 2
        assert isinstance(account.get_events()[0], Event)

        # Now access as a subclass with related properties
        reimbursements = account.get_events("reimbursement")
        assert len(reimbursements) == 1
        assert float(reimbursements[0].refund) == 2.32

        # Try filtering so that we get no reimbursements and empty qs
        reimbursements = account.get_events("reimbursement", refund=2.45)
        assert not reimbursements

        # Providing a dud event type should raise ValueError
        with pytest.raises(ValueError):
            account.add_event("foo")

    def test_list_persons(self):
        # create an account and associate two people with it
        account = Account.objects.create()
        pers1 = Person.objects.create(name="Foobar", slug="foo")
        pers2 = Person.objects.create(name="Bazbar", slug="bazbar")
        account.persons.add(pers1, pers2)

        # comma separated string, by name in alphabetical order
        assert account.list_persons() == "Bazbar, Foobar"

    def test_list_locations(self):
        # create an account and associate three addresses with it
        account = Account.objects.create()
        loc1 = Location.objects.create(name="Hotel Foo", city="Paris")
        loc2 = Location.objects.create(street_address="1 Foo St.", city="London")
        loc3 = Location.objects.create(city="Berlin")
        locations = [loc1, loc2, loc3]
        for location in locations:
            Address.objects.create(account=account, location=location)

        # semicolon separated string of locations with as much information as
        # possible; presented in database order.
        assert account.list_locations() == "Hotel Foo, Paris; 1 Foo St., London; Berlin"

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
        Subscription.objects.create(account=account, start_date=date2, end_date=date3)
        assert account.event_dates == [date1, date2, date3]

        # ignore partial dates with year unknown for borrow, purchase

        borrow = Borrow(account=account)
        # set partial start date with unknown year
        borrow.partial_start_date = "--05-03"
        borrow.save()
        # 1900 for date with unknown year should not be included
        assert account.event_dates == [date1, date2, date3]
        # partial end date with unknown years
        borrow.partial_start_date = None
        borrow.end_start_date = "--05-03"
        borrow.save()
        assert account.event_dates == [date1, date2, date3]

        purchase = Purchase(account=account)
        purchase.partial_start_date = "--06-15"
        purchase.save()
        # 1900 for date with unknown year should not be included
        assert account.event_dates == [date1, date2, date3]
        # partial end date with unknown years
        purchase.partial_start_date = None
        purchase.end_start_date = "--09-21"
        purchase.save()
        assert account.event_dates == [date1, date2, date3]

    def test_event_years(self):
        account = Account.objects.create()
        # multi-year subscription
        date1 = datetime.date(1927, 1, 1)
        date2 = datetime.date(1931, 1, 1)
        subs = Subscription.objects.create(
            account=account, start_date=date1, end_date=date2
        )
        assert account.event_years == [1927, 1928, 1929, 1930, 1931]

        # handle unset dates
        subs.end_date = None
        subs.save()
        assert account.event_years == [1927]

        # handle multiyear borrows *without* filling in years
        # (aka the james joyce rule)
        Borrow(account=account, start_date=date1, end_date=date2).save()
        assert set(account.event_years) == {1927, 1931}

    def test_earliest_date(self):
        account = Account.objects.create()
        # no date, no error
        assert not account.earliest_date()

        event1 = Subscription.objects.create(
            account=account,
            start_date=datetime.date(1943, 1, 1),
            end_date=datetime.date(1944, 1, 1),
        )
        event2 = Reimbursement.objects.create(
            account=account, start_date=datetime.date(1944, 5, 1)
        )

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
            account=account, start_date=datetime.date(1943, 1, 1)
        )
        assert account.last_date() == event.start_date

        # multiple events; use the last
        event1 = Subscription.objects.create(
            account=account,
            start_date=datetime.date(1943, 1, 1),
            end_date=datetime.date(1944, 1, 1),
        )
        event2 = Reimbursement.objects.create(
            account=account, start_date=datetime.date(1944, 5, 1)
        )

        assert account.last_date() == event2.end_date

    def test_subscription_set(self):
        account = Account.objects.create()
        assert isinstance(account.subscription_set, QuerySet)
        assert not account.subscription_set.exists()

        # add some events
        subs = Subscription.objects.create(
            account=account, start_date=datetime.date(1943, 1, 1)
        )
        subs2 = Subscription.objects.create(
            account=account,
            start_date=datetime.date(1943, 1, 1),
            end_date=datetime.date(1944, 1, 1),
        )
        reimb = Reimbursement.objects.create(
            account=account, start_date=datetime.date(1944, 5, 1)
        )
        generic = Event.objects.create(account=account)

        subscriptions = account.subscription_set
        assert subscriptions.count() == 2
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
        reimb1 = Reimbursement.objects.create(
            account=account,
            start_date=datetime.date(1943, 1, 1),
            end_date=None,
            refund=12.00,
        )
        reimb2 = Reimbursement.objects.create(
            account=account,
            start_date=datetime.date(1957, 1, 1),
            end_date=None,
            refund=15.00,
        )
        subs = Subscription.objects.create(
            account=account, start_date=datetime.date(1943, 1, 1)
        )
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

        src_type = SourceType.objects.get_or_create(name="Lending Library Card")[0]
        card = Bibliography.objects.create(
            bibliographic_note="John's library card", source_type=src_type
        )
        account.card = card
        assert account.has_card()

    def test_event_date_ranges(self):
        account = Account.objects.create()
        # no dates, no error
        assert account.event_date_ranges() == []

        # event with no dates - ignored
        Subscription.objects.create(account=account)
        assert account.event_date_ranges() == []

        # single range
        start = datetime.date(1923, 1, 1)
        end = datetime.date(1923, 5, 1)
        Subscription.objects.create(account=account, start_date=start, end_date=end)
        assert account.event_date_ranges() == [[start, end]]

        # event entirely within first range
        Borrow.objects.create(
            account=account,
            start_date=datetime.date(1923, 1, 21),
            end_date=datetime.date(1923, 2, 3),
        )
        # range should be unchanged
        assert account.event_date_ranges() == [[start, end]]

        # event date with year but no month should be ignored
        unknown_month = Subscription(account=account)
        unknown_month.partial_start_date = "1960"
        unknown_month.save()
        assert account.event_date_ranges() == [[start, end]]

        # event that starts within range and ends after
        borrow_end = datetime.date(1923, 6, 1)
        Borrow.objects.create(
            account=account, start_date=datetime.date(1923, 4, 21), end_date=borrow_end
        )
        # should extend the existing range
        assert account.event_date_ranges() == [[start, borrow_end]]
        # should ignore borrow dates if membership is specified
        assert account.event_date_ranges("membership") == [[start, end]]

        # event that starts the next day after the range ends
        sub2_start = datetime.date(1923, 6, 2)
        sub2_end = datetime.date(1923, 8, 1)
        Subscription.objects.create(
            account=account, start_date=sub2_start, end_date=sub2_end
        )
        # should extend the existing range
        assert account.event_date_ranges() == [[start, sub2_end]]

        # range with end but no start should be grouped within the range
        # and not sorted first in its own range because of no start date
        Subscription.objects.create(account=account, end_date=datetime.date(1923, 7, 1))
        assert account.event_date_ranges() == [[start, sub2_end]]

        # non-contiguous range should result in two ranges
        sub3_start = datetime.date(1924, 1, 5)
        sub3_end = datetime.date(1924, 3, 5)
        Subscription.objects.create(
            account=account, start_date=sub3_start, end_date=sub3_end
        )
        assert account.event_date_ranges() == [
            [start, sub2_end],
            [sub3_start, sub3_end],
        ]

        # event with only one date should be treated as a range
        borrow_start = datetime.date(1924, 6, 1)
        Borrow.objects.create(account=account, start_date=borrow_start, end_date=None)
        assert account.event_date_ranges() == [
            [start, sub2_end],
            [sub3_start, sub3_end],
            [borrow_start, borrow_start],
        ]

    def test_active_months(self):
        account = Account.objects.create()
        # no dates, no error
        assert account.active_months() == set()

        # add events to test
        Subscription.objects.create(
            account=account,
            start_date=datetime.date(1921, 1, 1),
            end_date=datetime.date(1921, 2, 1),
        )
        book1 = Work.objects.create()
        Borrow.objects.create(
            account=account, work=book1, start_date=datetime.date(1921, 4, 10)
        )
        # borrow with unknown month should be ignored
        month_unknown = Borrow.objects.create(account=account, work=book1)
        month_unknown.partial_start_date = "1930"
        month_unknown.save()
        Reimbursement.objects.create(
            account=account, start_date=datetime.date(1922, 1, 1)
        )

        assert account.active_months() == set(["192101", "192102", "192104", "192201"])
        assert account.active_months("membership") == set(
            ["192101", "192102", "192201"]
        )
        assert account.active_months("books") == set(["192104"])

    def test_member_card_images(self):
        account = Account()
        # should be empty, but not error
        assert isinstance(account.member_card_images(), EmptyQuerySet)

        # add card, manifest, canvases
        test_manifest = Manifest.objects.create(short_id="m1")
        img1 = Canvas.objects.create(manifest=test_manifest, order=1, short_id="i1")
        img2 = Canvas.objects.create(manifest=test_manifest, order=2, short_id="i2")
        src_type = SourceType.objects.get_or_create(name="Lending Library Card")[0]
        card = Bibliography.objects.create(
            bibliographic_note="Jane's library card",
            source_type=src_type,
            manifest=test_manifest,
        )
        account.card = card
        account.save()

        card_images = account.member_card_images()
        assert card_images
        assert card_images.count() == 2
        assert img1 in card_images
        assert img2 in card_images

        # add an image to a different manifest
        manifest2 = Manifest.objects.create(short_id="m2")
        other_img = Canvas.objects.create(manifest=manifest2, short_id="other", order=1)
        assert other_img not in account.member_card_images()
        # link via event + footnote
        event = Event.objects.create(account=account)
        # event_ctype = ContentType.objects.get_for_model(Event)
        fn = Footnote.objects.create(
            content_object=event,
            # object_id=event, content_type=event_ctype,
            image=other_img,
            bibliography=card,
        )
        event.footnotes.add(fn)
        card_images = account.member_card_images()
        assert other_img in card_images
        # should come after main card images
        assert card_images[0] == img1
        assert card_images[1] == img2
        assert card_images[2] == other_img


class TestAddress(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Hotel de la Rue")
        self.account = Account.objects.create()

        self.address = Address.objects.create(
            location=self.location, account=self.account
        )

    def test_repr(self):
        new_addr = Address(location=self.location)
        assert repr(new_addr) == "<Address pk:?? %s>" % new_addr

        assert repr(self.address) == "<Address pk:%s %s>" % (
            self.address.pk,
            self.address,
        )

    def test_str(self):
        # account only
        assert str(self.address) == "%s — %s" % (self.location, self.account)

        # account with start date
        start_year = 1920
        self.address.start_date = datetime.datetime(year=start_year, month=1, day=1)
        assert str(self.address) == "%s — %s (%s – )" % (
            self.location,
            self.account,
            start_year,
        )

        # start and end date
        end_year = 1923
        self.address.end_date = datetime.datetime(year=end_year, month=1, day=1)
        assert str(self.address) == "%s — %s (%d – %d)" % (
            self.location,
            self.account,
            start_year,
            end_year,
        )

        # end date only
        self.address.start_date = None
        assert str(self.address) == "%s — %s ( – %d)" % (
            self.location,
            self.account,
            end_year,
        )

        # care of person
        self.address.care_of_person = Person.objects.create(name="Jones", slug="jones")
        assert str(self.address) == "%s — %s ( – %d) c/o %s" % (
            self.location,
            self.account,
            end_year,
            self.address.care_of_person,
        )
        # care of, no dates
        self.address.end_date = None
        assert str(self.address) == "%s — %s c/o %s" % (
            self.location,
            self.account,
            self.address.care_of_person,
        )

        # person, no account
        self.address.account = None
        self.address.person = Person.objects.create(name="Smith", slug="sm")
        assert str(self.address) == "%s — %s c/o %s" % (
            self.location,
            self.address.person,
            self.address.care_of_person,
        )

    def test_clean(self):
        addr = Address(location=self.location)
        # no account or person is an error
        with pytest.raises(ValidationError):
            addr.clean()
        addr.account = self.account
        addr.person = Person.objects.create(name="Lee", slug="lee")

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
        self.work = Work.objects.create(title="Selected poems")
        self.event = Event.objects.create(account=self.account)

    def test_repr(self):
        assert repr(self.event) == "<Event pk:%s account:%s %s>" % (
            self.event.pk,
            self.account.pk,
            self.event.date_range,
        )

        # test one subclass
        borrow = Borrow.objects.create(account=self.account, work=self.work)
        assert repr(borrow) == "<Borrow pk:%s account:%s %s>" % (
            borrow.pk,
            self.account.pk,
            borrow.date_range,
        )

    def test_str(self):
        assert str(self.event) == "Event for account #%s ??/??" % self.account.pk

    def test_date_range(self):
        assert self.event.date_range == "??/??"

        # start only
        self.event.start_date = datetime.date(2018, 5, 1)
        assert self.event.date_range == "%s/??" % self.event.start_date.isoformat()

        # both start and end set, different values
        self.event.end_date = datetime.date(2020, 6, 11)
        assert self.event.date_range == "{}/{}".format(
            self.event.start_date, self.event.end_date
        )

        # both set, same values
        self.event.end_date = self.event.start_date
        assert self.event.date_range == self.event.start_date.isoformat()

        # end date only
        self.event.start_date = None
        assert self.event.date_range == "??/{}".format(self.event.end_date.isoformat())

    def test_event_type(self):
        assert self.event.event_type == "Generic"
        # Create a subscription and check its generic event type
        subscription = Subscription.objects.create(
            account=self.account, duration=1, volumes=2, price_paid=3.20
        )
        # subscription, not otherwise specified
        assert subscription.event_ptr.event_type == "Subscription"
        # subscription labeled as a supplement
        subscription.subtype = Subscription.SUPPLEMENT
        subscription.save()
        assert subscription.event_ptr.event_type == "Supplement"
        # subscription labeled as a renewal
        subscription.subtype = Subscription.RENEWAL
        subscription.save()
        assert subscription.event_ptr.event_type == "Renewal"

        # Create a reimbursement check its event type
        reimbursement = Reimbursement.objects.create(
            account=self.account, refund=2.30, currency="USD"
        )
        assert reimbursement.event_ptr.event_type == "Reimbursement"

        # borrow
        borrow = Borrow.objects.create(account=self.account, work=self.work)
        assert borrow.event_ptr.event_type == "Borrow"

        # purchase
        purchase = Purchase.objects.create(
            account=self.account, work=self.work, price=5
        )
        assert purchase.event_ptr.event_type == "Purchase"

    def test_event_label(self):
        ev = Event(account=self.account)
        assert ev.event_label == "Generic"
        ev = Event(account=self.account, notes="NOTATION: STRIKETHRU")
        assert ev.event_label == "Crossed out"
        ev = Event(
            account=self.account, notes="other info NOTATION: SBGIFT; more details"
        )
        assert ev.event_label == "Gift"
        # other event types should still come through
        subs = Subscription.objects.create(account=self.account)
        assert subs.event_ptr.event_label == "Subscription"
        # but notation takes precedence over type
        borrow = Borrow.objects.create(account=self.account)
        borrow.notes = "NOTATION: SOLDFOR"
        assert borrow.event_label == "Purchase"


class TestEventQuerySet(TestCase):
    def setUp(self):
        # create account with test events
        acct = Account.objects.create()
        # create one event of each type to test with
        self.event_types = {
            "subscription": Subscription.objects.create(account=acct),
            "reimbursement": Reimbursement.objects.create(account=acct),
            "borrow": Borrow.objects.create(account=acct),
            "purchase": Purchase.objects.create(account=acct),
            "generic": Event.objects.create(account=acct),
        }

    def test_generic(self):
        assert Event.objects.generic().count() == 1
        assert self.event_types["generic"] in Event.objects.generic()

    def test_subscriptions(self):
        assert Event.objects.subscriptions().count() == 1
        assert (
            self.event_types["subscription"].event_ptr in Event.objects.subscriptions()
        )

    def test_reimbursements(self):
        assert Event.objects.reimbursements().count() == 1
        assert (
            self.event_types["reimbursement"].event_ptr
            in Event.objects.reimbursements()
        )

    def test_borrows(self):
        assert Event.objects.borrows().count() == 1
        assert self.event_types["borrow"].event_ptr in Event.objects.borrows()

    def test_purchases(self):
        assert Event.objects.purchases().count() == 1
        assert self.event_types["purchase"].event_ptr in Event.objects.purchases()

    def test_membership_activities(self):
        # one subscription, one reimbursement
        assert Event.objects.membership_activities().count() == 2
        assert (
            self.event_types["subscription"].event_ptr
            in Event.objects.membership_activities()
        )
        assert (
            self.event_types["reimbursement"].event_ptr
            in Event.objects.membership_activities()
        )

    def test_known_years(self):
        # all years partial date flag currently unset; should return all
        assert Event.objects.known_years().count() == Event.objects.all().count()

        # partial date, known year
        self.event_types["subscription"].partial_start_date = "1919-11"
        self.event_types["subscription"].save()
        # partial date, unknown year for start date
        self.event_types["reimbursement"].partial_start_date = "--12-01"
        self.event_types["reimbursement"].save()
        self.event_types["borrow"].start_date = datetime.date(1942, 5, 1)
        self.event_types["borrow"].save()
        # unknown year for end date
        self.event_types["generic"].partial_end_date = "--02-13"
        self.event_types["generic"].save()

        known_year_events = Event.objects.known_years()
        assert self.event_types["subscription"].event_ptr in known_year_events
        assert self.event_types["reimbursement"].event_ptr not in known_year_events
        assert self.event_types["borrow"].event_ptr in known_year_events
        assert self.event_types["generic"] not in known_year_events


class TestSubscription(TestCase):
    def setUp(self):
        self.account = Account.objects.create()
        self.subscription = Subscription.objects.create(
            account=self.account,
            start_date=datetime.date(1940, 4, 8),
            duration=1,
            volumes=2,
            price_paid=3.20,
        )

    def test_str(self):
        assert str(self.subscription) == "Subscription for account #%s %s/??" % (
            self.subscription.account.pk,
            self.subscription.start_date.isoformat(),
        )

    def test_validate_unique(self):
        # resaving existing record should not error
        self.subscription.validate_unique()

        # creating new subscription for same account & date should error
        with pytest.raises(ValidationError):
            subscr = Subscription(
                account=self.account, start_date=self.subscription.start_date
            )
            subscr.validate_unique()

        # creating new subscription for same account with same
        # start date AND end date should error
        with pytest.raises(ValidationError):
            subscr = Subscription(
                account=self.account,
                start_date=self.subscription.start_date,
                end_date=self.subscription.end_date,
            )
            subscr.validate_unique()

        # same account, type, start date but different end date is valid
        subscr = Subscription(
            account=self.account,
            start_date=self.subscription.start_date,
            end_date=datetime.date(1931, 3, 6),
        )
        subscr.validate_unique()

        # same account + date with different subtype should be fine
        subscr = Subscription(
            account=self.account, start_date=self.subscription.start_date, subtype="ren"
        )
        subscr.validate_unique()

    def test_calculate_duration(self):
        # create subscription with start date of today and
        # adjust end date to test duration calculations
        today = datetime.datetime.now()

        # single day
        delta = relativedelta(days=3)
        subs = Subscription(start_date=today, end_date=today + delta)
        duration = subs.calculate_duration()
        expect = 3
        assert duration == expect, "%s should generate duration of '%d', got '%d'" % (
            delta,
            expect,
            duration,
        )

        # month duration should be actual day count
        # February in a non-leap year; 28 days
        subs = Subscription(
            start_date=datetime.date(2017, 2, 1), end_date=datetime.date(2017, 3, 1)
        )
        duration = subs.calculate_duration()
        expect = 28
        assert (
            duration == expect
        ), "Month of February should generate duration of '%d', got '%d'" % (
            expect,
            duration,
        )
        # January in any year; 31 days
        subs = Subscription(
            start_date=datetime.date(2017, 1, 1), end_date=datetime.date(2017, 2, 1)
        )
        duration = subs.calculate_duration()
        expect = 31
        assert (
            duration == expect
        ), "Month of January should generate duration of '%d', got '%d'" % (
            expect,
            duration,
        )

    def test_calculate_duration_partial_dates(self):
        subs = Subscription()
        # month/day partial dates in (assumed) same year
        subs.partial_start_date = "--11-05"
        subs.partial_end_date = "--12-05"
        assert subs.calculate_duration() == 30

        # month/day partial dates that span new year's
        subs.partial_start_date = "--12-02"
        subs.partial_end_date = "--01-02"
        assert subs.calculate_duration() == 31

        # mixed precision
        subs.partial_start_date = "1932-12-02"
        subs.partial_end_date = "--01-02"
        assert not subs.calculate_duration()

        # unsupported precision
        subs.partial_start_date = "1932-12"
        subs.partial_end_date = "1933-01"
        assert not subs.calculate_duration()

    def test_save(self):
        acct = Account.objects.create()
        subs = Subscription(account=acct)

        # test that calculate duration is called when it should be
        with patch.object(subs, "calculate_duration") as mock_calcdur:
            # return an arbitrary integer value so save does not error
            mock_calcdur.return_value = 30

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
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "1 day"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )
        # two days
        delta = relativedelta(days=2)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "2 days"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )

        # single month
        delta = relativedelta(months=1)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "1 month"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )
        # multiple months
        delta = relativedelta(months=6)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "6 months"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )

        # single year
        delta = relativedelta(years=1)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "1 year"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )
        # multiple years
        delta = relativedelta(years=2)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "2 years"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )

        # one week
        delta = relativedelta(days=7)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "1 week"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )
        # two weeks
        delta = relativedelta(days=7 * 2)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "2 weeks"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )
        # six weeks
        delta = relativedelta(days=7 * 6)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "6 weeks"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )

        # combined units
        delta = relativedelta(years=1, days=3)
        subs = Subscription.objects.create(
            account=acct, start_date=today, end_date=today + delta
        )
        dur = subs.readable_duration()
        expect = "1 year, 3 days"
        assert dur == expect, "%s should display as '%s', got '%s'" % (
            delta,
            expect,
            dur,
        )

        # special cases
        # test February in a non-leap year; 28 days, should display as one month
        subs = Subscription.objects.create(
            account=acct,
            start_date=datetime.date(2017, 2, 1),
            end_date=datetime.date(2017, 3, 1),
        )
        dur = subs.readable_duration()
        expect = "1 month"
        assert dur == expect, "Month of February should display as '%s', got '%s'" % (
            expect,
            dur,
        )

    def test_total_amount(self):
        # price paid, no deposit
        assert self.subscription.total_amount() == 3.20

        # add a deposit amount
        self.subscription.deposit = 5.70
        assert self.subscription.total_amount() == 8.90

        # remove price
        self.subscription.price_paid = None
        assert self.subscription.total_amount() == 5.70


class TestPurchase(TestCase):
    def setUp(self):
        self.account = Account.objects.create()
        self.purchase = Purchase(
            account=self.account,
            price=2.30,
            currency="USD",
            work=Work.objects.create(title="Le Foo"),
        )
        self.purchase.calculate_date("start_date", "1920-02-03")
        self.purchase.save()

    def test_str(self):
        assert str(self.purchase) == (
            "Purchase for account #%s 1920-02-03" % self.purchase.account.pk
        )

    def test_date(self):
        assert self.purchase.date() == self.purchase.date_range

    def test_save(self):
        # no end date or precision
        self.purchase.end_date = None
        self.purchase.end_date_precision = None
        self.purchase.save()
        # save should set end_date and end_date_precision
        assert self.purchase.end_date == self.purchase.start_date
        assert self.purchase.end_date_precision == self.purchase.start_date_precision


class TestReimbursement(TestCase):
    def setUp(self):
        self.account = Account.objects.create()
        self.reimbursement = Reimbursement.objects.create(
            account=self.account,
            refund=2.30,
            currency="USD",
        )

    def test_str(self):
        assert (
            str(self.reimbursement)
            == "Reimbursement for account #%s ??/??" % self.reimbursement.account.pk
        )

    def test_date(self):
        self.reimbursement.start_date = datetime.date(1920, 1, 1)
        self.reimbursement.save()
        assert self.reimbursement.date() == self.reimbursement.partial_start_date

    def test_validate_unique(self):
        # resaving existing record should not error
        self.reimbursement.validate_unique()

        # creating new reimbursement for same account & date & amount should error
        with pytest.raises(ValidationError):
            reimburse = Reimbursement(
                account=self.account,
                start_date=self.reimbursement.start_date,
                refund=self.reimbursement.refund,
            )
            reimburse.validate_unique()

        # a new reimbursement that is not on the same date should not be caught
        reimburse = Reimbursement(
            account=self.account, start_date=datetime.date(1919, 1, 1)
        )
        reimburse.validate_unique()

        # same account, same day, different refund amount is allowed
        reimburse2 = Reimbursement(
            account=self.account, start_date=self.reimbursement.start_date, refund=100
        )
        reimburse.validate_unique()

        # a reimbursement without an account should not raise
        # a related object error
        Reimbursement().validate_unique()

    def test_auto_end_date(self):
        self.reimbursement.start_date = datetime.datetime.now()
        self.reimbursement.save()
        assert self.reimbursement.end_date == self.reimbursement.end_date

        self.reimbursement.start_date = None
        self.reimbursement.save()
        assert not self.reimbursement.end_date

        # partial dates
        self.reimbursement.partial_start_date = "1942-01"
        self.reimbursement.end_date = None
        self.reimbursement.save()
        assert (
            self.reimbursement.partial_end_date == self.reimbursement.partial_start_date
        )


class TestBorrow(TestCase):
    def setUp(self):
        self.account = Account.objects.create()
        self.work = Work.objects.create(title="Collected works")
        self.borrow = Borrow.objects.create(account=self.account, work=self.work)

    def test_str(self):
        assert str(self.borrow) == (
            "Borrow for account #%s ??/??" % self.borrow.account.pk
        )

        start_date = datetime.date(2018, 5, 1)
        self.borrow.partial_start_date = start_date.isoformat()
        assert str(self.borrow).endswith("%s/??" % start_date.isoformat())

        # handle partial dates
        self.borrow.partial_start_date = "2018-05"
        assert str(self.borrow).endswith("%s/??" % self.borrow.partial_start_date)

    def test_save(self):
        today = datetime.date.today()
        borrow = Borrow(account=self.account, work=self.work)
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


class TestCurrencyMixin(TestCase):
    # create test currency model to test mixin behavior
    class CurrencyObject(CurrencyMixin):
        class Meta:
            app_label = "test"

    def test_currency_symbol(self):
        coin = self.CurrencyObject()
        # default value is Franc
        assert coin.currency_symbol() == "₣"

        coin.currency = CurrencyMixin.USD
        assert coin.currency_symbol() == "$"

        coin.currency = CurrencyMixin.GBP
        assert coin.currency_symbol() == "£"

        coin.currency = ""
        assert coin.currency_symbol() == ""

        # not a valid choice, but test fallback display behavior
        # when symbol is not known
        coin.currency = "foo"
        assert coin.currency_symbol() == "foo"
