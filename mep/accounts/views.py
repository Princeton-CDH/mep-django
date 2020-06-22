import datetime
from collections import defaultdict

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
        date_start = date - relativedelta(years=100)
        # determine end date for tweets to review
        date_end = date_start + relativedelta(weeks=4)

        events = Event.objects \
            .filter(Q(start_date__gte=date_start,
                      start_date__lte=date_end) |
                    Q(subscription__purchase_date__gte=date_start,
                      subscription__purchase_date__lte=date_end) |
                    Q(borrow__isnull=False, end_date__gte=date_start,
                      end_date__lte=date_end)) \
            .filter(Q(start_date_precision__isnull=True) |
                    Q(start_date_precision=int(self.full_precision)))

        return events

    def get_context_data(self):
        context = super().get_context_data()

        # construct a dictionary of dates with a list of events,
        # to make it easy to display all tweets in order
        events_by_date = defaultdict(list)

        for ev in self.object_list:
            if ev.event_label in ['Subscription', 'Renewal']:
                events_by_date[ev.subscription.partial_purchase_date].append(ev)
            elif ev.event_label == 'Borrow':
                events_by_date[ev.partial_start_date].append(ev)
                events_by_date[ev.partial_end_date].append(ev)
            else:
                events_by_date[ev.partial_start_date].append(ev)

        # could include unset dates; remove them
        # NOTE: could include dates out of the current range; do we care?
        del events_by_date[None]

        # convert to a standard dict to avoid problems with django templates;
        # sort by date so review will be sequential
        events_by_date = {k: events_by_date[k] for k in sorted(events_by_date)}
        context['events_by_date'] = events_by_date
        return context
