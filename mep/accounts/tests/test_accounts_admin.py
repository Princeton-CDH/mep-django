import datetime

from dateutil.relativedelta import relativedelta
from django.test import TestCase

from mep.accounts.models import Account, Subscription, Borrow, DatePrecision
from mep.accounts.admin import SubscriptionAdminForm, BorrowAdminForm


class TestSubscriptionAdminForm(TestCase):

    def test_get_initial_for_field(self):
        subs = Subscription(duration=5, start_date=datetime.date.today())
        form = SubscriptionAdminForm(instance=subs)

        # customized initial value
        assert form.get_initial_for_field(form.fields['duration_units'],
            'duration_units') == subs.readable_duration()
        # default behavior for other fields
        assert form.get_initial_for_field(form.fields['duration'],
            'duration') == subs.duration

    def test_validation(self):
        acct = Account.objects.create()
        subs = Subscription(duration=5, start_date=datetime.date.today())
        form_data = {
            'account': acct.id,
            'duration_units': '1 week'
        }
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert form.is_valid()

        form_data['duration_units'] = '34  months '
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert form.is_valid()

        form_data['duration_units'] = '2 decades'
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert not form.is_valid()

    def test_clean(self):
        acct = Account.objects.create()
        subs = Subscription(duration=5, start_date=datetime.date.today())
        form_data = {
            'account': acct.id,
            'duration_units': '1 week',
            'duration': subs.duration,
            'start_date': subs.start_date,
            'end_date': None
        }
        form = SubscriptionAdminForm(form_data, instance=subs)
        # validate so cleaned data will be available
        assert form.is_valid()

        # check that end date is set
        assert 'end_date' in form.cleaned_data
        # and calculated correctly
        assert form.cleaned_data['end_date'] == \
            subs.start_date + relativedelta(days=7)

        # when start date and end date are both set, duration should be ignored
        form_data['end_date'] = subs.start_date + relativedelta(days=3)
        form_data['duration_units'] = '6 months'
        form = SubscriptionAdminForm(form_data, instance=subs)
        assert form.is_valid()
        assert form.cleaned_data['end_date'] == form_data['end_date']


class TestPartialDateFormMixin(TestCase):

    # Testing PartialDateFormMixin via Borrow, since we need a concrete model
    # to run validation checks against.

    def test_get_initial_for_field(self):
        acct = Account.objects.create()
        acct.save()
        borrow = Borrow(account=acct)
        borrow.partial_start_date = '--05-03'
        borrow.partial_end_date = '1900-05'
        form = BorrowAdminForm(instance=borrow)
        # ensure that partial dates are auto-populated correctly
        assert form.get_initial_for_field(form.fields['partial_start_date'],
            'partial_start_date') == borrow.partial_start_date
        assert form.get_initial_for_field(form.fields['partial_end_date'],
            'partial_end_date') == borrow.partial_end_date
        # shouldn't affect other fields
        assert form.get_initial_for_field(form.fields['account'],
            'account') == borrow.account.id

    def test_validation(self):
        acct = Account.objects.create()
        acct.save()
        borrow = Borrow(account=acct)

        #
        # valid partial date forms
        #
        # yyyy-mm-dd (full precision)
        form_data = {
            'partial_start_date': '1901-05-03',
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        # yyyy-mm (year and month)
        form_data = {
            'partial_start_date': '1901-05',
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        # yyyy (year only)
        form_data = {
            'partial_start_date': '1901',
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        # --mm--dd (month and day)
        form_data = {
            'partial_start_date': '--05-03',
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        # empty string (clear the date)
        form_data = {
            'partial_start_date': '',
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()

        #
        # invalid forms
        #
        # some other type of string
        form_data = {
            'partial_start_date': 'definitely_not_a_date',
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert not form.is_valid()
        # yyyy--dd (year and day)
        form_data = {
            'partial_start_date': '1901--03',
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert not form.is_valid()
        # dd or mm (month or day only)
        form_data = {
            'partial_start_date': '05',
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert not form.is_valid()

        # number that's not a valid month
        form_data = {
            'partial_start_date': '1901-08-34',
            'account': acct.id
        }
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
            'partial_start_date': '1901-05-03', # yyyy-mm-dd (full precision)
            'partial_end_date': '--05-03', # --mm--dd (month and day)
            'account': acct.id
        }
        form = BorrowAdminForm(form_data, instance=borrow)
        assert form.is_valid()
        form.clean()
        # dates and precision should get correctly set through the descriptor
        assert borrow.start_date == datetime.date(1901, 5, 3)
        assert borrow.start_date_precision == DatePrecision.year | DatePrecision.month | DatePrecision.day
        assert borrow.end_date == datetime.date(1900, 5, 3)
        assert borrow.end_date_precision == DatePrecision.month | DatePrecision.day
