import datetime

from dateutil.relativedelta import relativedelta
from django.test import TestCase

from mep.accounts.partial_date import DatePrecision
from mep.accounts.models import (
    Account,
    Subscription,
    Borrow,
    Event,
    Purchase,
    Reimbursement,
)
from mep.accounts.admin import (
    SubscriptionAdminForm,
    BorrowAdminForm,
    EventAdmin,
    EventTypeListFilter,
)


class TestSubscriptionAdminForm(TestCase):
    def test_get_initial_for_field(self):
        subs = Subscription(duration=5, start_date=datetime.date.today())
        form = SubscriptionAdminForm(instance=subs)

        # customized initial value
        assert (
            form.get_initial_for_field(form.fields["duration_units"], "duration_units")
            == subs.readable_duration()
        )
        # default behavior for other fields
        assert (
            form.get_initial_for_field(form.fields["duration"], "duration")
            == subs.duration
        )

    def test_validation(self):
        acct = Account.objects.create()
        subs = Subscription(duration=5, start_date=datetime.date.today())
        form_data = {"account": acct.id, "duration_units": "1 week"}
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert form.is_valid()

        form_data["duration_units"] = "34  months "
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert form.is_valid()

        form_data["duration_units"] = "2 decades"
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert not form.is_valid()

    def test_clean(self):
        acct = Account.objects.create()
        today = datetime.date.today()
        subs = Subscription(duration=5, account=acct, start_date=today)
        form_data = {
            "account": acct.id,
            "duration_units": "1 week",
            "duration": subs.duration,
            "partial_start_date": subs.start_date.isoformat(),
            "partial_end_date": None,
        }
        form = SubscriptionAdminForm(form_data, instance=subs)
        # validate so cleaned data will be available
        assert form.is_valid()

        # check that end date is set
        cleaned_data = form.clean()
        assert "partial_end_date" in cleaned_data
        # and calculated correctly
        assert (
            form.instance.partial_end_date
            == (today + relativedelta(days=7)).isoformat()
        )
        assert (
            cleaned_data["partial_end_date"]
            == (today + relativedelta(days=7)).isoformat()
        )

        # when start date and end date are both set, duration should be ignored
        form_data["partial_end_date"] = (today + relativedelta(days=3)).isoformat()
        form_data["duration_units"] = "6 months"
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert form.is_valid()
        cleaned_data = form.clean()
        assert cleaned_data["partial_end_date"] == form_data["partial_end_date"]

        # handle partial dates correctly
        form_data["partial_start_date"] = "1923-01"
        form_data["partial_end_date"] = None
        form_data["duration_units"] = "6 months"
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert form.is_valid()
        cleaned_data = form.clean()
        assert cleaned_data["partial_end_date"] == "1923-07"


class TestPartialDateFormMixin(TestCase):
    # Testing PartialDateFormMixin via Borrow, since we need a concrete model
    # to run validation checks against.

    def test_get_initial_for_field(self):
        acct = Account.objects.create()
        acct.save()
        borrow = Borrow(account=acct)
        borrow.partial_start_date = "--05-03"
        borrow.partial_end_date = "1900-05"
        form = BorrowAdminForm(instance=borrow)
        # ensure that partial dates are auto-populated correctly
        assert (
            form.get_initial_for_field(
                form.fields["partial_start_date"], "partial_start_date"
            )
            == borrow.partial_start_date
        )
        assert (
            form.get_initial_for_field(
                form.fields["partial_end_date"], "partial_end_date"
            )
            == borrow.partial_end_date
        )
        # shouldn't affect other fields
        assert (
            form.get_initial_for_field(form.fields["account"], "account")
            == borrow.account.id
        )

    def test_validation(self):
        acct = Account.objects.create()
        acct.save()
        borrow = Borrow(account=acct)

        #
        # valid partial date forms
        #
        # yyyy-mm-dd (full precision)
        form_data = {"partial_start_date": "1901-05-03", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        # yyyy-mm (year and month)
        form_data = {"partial_start_date": "1901-05", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        # yyyy (year only)
        form_data = {"partial_start_date": "1901", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        # --mm--dd (month and day)
        form_data = {"partial_start_date": "--05-03", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        # empty string (clear the date)
        form_data = {"partial_start_date": "", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()

        #
        # invalid forms
        #
        # some other type of string
        form_data = {"partial_start_date": "definitely_not_a_date", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert not form.is_valid()
        # yyyy--dd (year and day)
        form_data = {"partial_start_date": "1901--03", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert not form.is_valid()
        # dd or mm (month or day only)
        form_data = {"partial_start_date": "05", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert not form.is_valid()

        # number that's not a valid month
        form_data = {"partial_start_date": "1901-08-34", "account": acct.id}
        form = BorrowAdminForm(form_data, instance=borrow)
        assert not form.is_valid()

    def test_clean(self):
        acct = Account.objects.create()
        acct.save()
        borrow = Borrow(account=acct)
        # a newly created borrow should have None for all date values
        assert borrow.start_date is None
        assert borrow.end_date is None
        assert borrow.start_date_precision is None
        assert borrow.end_date_precision is None
        # fill out some valid partial dates for start and end
        form_data = {
            "partial_start_date": "1901-05-03",  # yyyy-mm-dd (full precision)
            "partial_end_date": "--05-03",  # --mm--dd (month and day)
            "account": acct.id,
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        form.clean()
        # dates and precision should get correctly set through the descriptor
        assert borrow.start_date == datetime.date(1901, 5, 3)
        assert (
            borrow.start_date_precision
            == DatePrecision.year | DatePrecision.month | DatePrecision.day
        )
        assert borrow.end_date == datetime.date(1900, 5, 3)
        assert borrow.end_date_precision == DatePrecision.month | DatePrecision.day


class TestEventTypeListFilter(TestCase):
    def test_queryset(self):
        # create test events
        acct = Account.objects.create()
        acct.save()
        # create one event of each type to test with
        event_types = {
            "subscription": Subscription.objects.create(account=acct),
            "reimbursement": Reimbursement.objects.create(account=acct),
            "borrow": Borrow.objects.create(account=acct),
            "purchase": Purchase.objects.create(account=acct),
            "generic": Event.objects.create(account=acct),
        }

        for event_type, event_obj in event_types.items():
            # create event type filter for requested event type
            efilter = EventTypeListFilter(
                None, {"event_type": [event_type]}, Event, EventAdmin
            )
            qs = efilter.queryset(None, Event.objects.all())
            assert qs.count() == 1
            # generic event *is* an event object
            if event_type == "generic":
                assert event_obj in qs
            # everything else is a subclass with a pointer to event
            else:
                assert event_obj.event_ptr in qs

        # unfiltered
        efilter = EventTypeListFilter(None, {}, Event, EventAdmin)
        assert efilter.queryset(None, Event.objects.all()).count() == len(event_types)
