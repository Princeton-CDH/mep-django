import datetime
from collections import defaultdict, OrderedDict

from dal import autocomplete
from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView

from mep.accounts.models import Account, Event
from mep.accounts.partial_date import DatePrecision


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


class Twitter100yearsReview(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'accounts/100years_twitter_review.html'

    full_precision = DatePrecision.year | DatePrecision.month | \
        DatePrecision.day

    def get_date_range(self):
        '''Determine start and end date for events to review. Start
        100 years before today, end 4 weeks after that.'''
        # determine date exactly 100 years earlier
        self.date_start = datetime.date.today() - relativedelta(years=100)
        # determine end date for tweets to review
        self.date_end = self.date_start + relativedelta(months=3)

        return self.date_start, self.date_end

    def get_queryset(self):
        date_start, date_end = self.get_date_range()

        events = Event.objects \
            .filter(Q(start_date__gte=date_start,
                      start_date__lte=date_end) |
                    Q(subscription__purchase_date__gte=date_start,
                      subscription__purchase_date__lte=date_end) |
                    Q(borrow__isnull=False, end_date__gte=date_start,
                      end_date__lte=date_end)) \
            .filter(Q(start_date_precision__isnull=True) |
                    Q(start_date_precision=int(self.full_precision))) \
            .exclude(work__notes__contains="UNCERTAINTYICON")

        return events

    def get_context_data(self):
        context = super().get_context_data()

        # construct a dictionary of dates with a list of events,
        # to make it easy to display all tweets in order
        events_by_date = defaultdict(list)

        for ev in self.object_list:
            if ev.event_label in ['Subscription', 'Renewal']:
                events_by_date[
                    ev.subscription.partial_purchase_date].append(ev)
            elif ev.event_label == 'Borrow':
                events_by_date[ev.partial_start_date].append(ev)
                events_by_date[ev.partial_end_date].append(ev)
            else:
                events_by_date[ev.partial_start_date].append(ev)

        # could include None for unset dates; remove without error
        events_by_date.pop(None, None)

        # convert to a standard dict to avoid problems with django templates;
        # sort by date & converted to ordered dict so review will be sequential
        # filter out any dates before the current range
        date_start_iso = self.date_start.isoformat()
        date_end_iso = self.date_end.isoformat()
        events_by_date = OrderedDict([
            (k, events_by_date[k])
            for k in sorted(events_by_date)
            if k and date_start_iso <= k <= date_end_iso])
        context['events_by_date'] = events_by_date
        return context
