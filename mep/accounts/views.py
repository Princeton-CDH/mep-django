import datetime

from dal import autocomplete
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.views.generic import ListView

from mep.accounts.models import Account, Event
from mep.accounts.partial_date import DatePrecision
from mep.common.views import LoginRequiredOr404Mixin


class AccountAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.accounts.models.Account` in address many-to-many'''

    def get_queryset(self):
        '''Get a queryset filtered by query string. Searches on account id,
        people associated with account, and addresses associated with account
        '''

        return Account.objects.filter(
            Q(id__contains=self.q) |
            Q(persons__name__icontains=self.q) |
            Q(persons__mep_id__icontains=self.q) |
            Q(locations__name__icontains=self.q) |
            Q(locations__street_address__icontains=self.q) |
            Q(locations__city__icontains=self.q)
        ).distinct().order_by('id')


class Twitter100yearsReview(LoginRequiredOr404Mixin, ListView):
    model = Event
    template_name = 'accounts/100years_twitter_review.html'

    full_precision = DatePrecision.year | DatePrecision.month | \
        DatePrecision.day

    def get_queryset(self):
        date = datetime.date.today()
        # determine date 100 years earlier
        date = date - relativedelta(years=100)
        two_weeks_ahead = date + relativedelta(weeks=4)
        return super().get_queryset() \
            .filter(start_date__gte=date,
                    start_date__lte=two_weeks_ahead) \
            .filter(Q(start_date_precision__isnull=True) |
                    Q(start_date_precision=int(self.full_precision))) \
            .order_by('start_date', 'account')
