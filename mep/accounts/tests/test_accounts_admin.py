import datetime

from dateutil.relativedelta import relativedelta
from django.test import TestCase

from mep.accounts.models import Account, Subscription
from mep.accounts.admin import SubscriptionAdminForm


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

