import datetime
import subprocess
import sys

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.urls import reverse
import tweepy

from mep.accounts.models import Event
from mep.accounts.partial_date import DatePrecision
from mep.common.utils import absolutize_url


class Command(BaseCommand):

    # date format:  Saturday, May 8, 1920
    date_format = '%A, %B %-d, %Y'

    full_precision = DatePrecision.year | DatePrecision.month | \
        DatePrecision.day

    def add_arguments(self, parser):
        parser.add_argument('mode', choices=['report', 'schedule', 'tweet'])
        parser.add_argument(
            '-d', '--date',
            help='Specify an alternate date in YYYY-MM-DD format. ' +
                 '(default is today)')
        parser.add_argument(
            '-e', '--event', type=int,
            help='Database id for the event to be tweeted. ' +
                 '(Required for tweet mode)')

    def handle(self, *args, **kwargs):
        date = self.get_date(**kwargs)

        if kwargs['mode'] == 'report':
            self.report(date)
        elif kwargs['mode'] == 'schedule':
            self.schedule(date)
        elif kwargs['mode'] == 'tweet':
            # todo tweet single event
            try:
                ev = Event.objects.get(pk=kwargs['event'])
                self.tweet(ev, date)
            except Event.DoesNotExist:
                self.stderr.write('Error: event %s not found' % kwargs['event'])

    def get_date(self, **kwargs):
        # find events relative to the specified day if set
        date = kwargs.get('date', None)
        # TODO: determine if server time is UTC or local

        # only allow overriding date for report
        if date and kwargs['mode'] == 'report':
            relative_date = datetime.date(*[int(n) for n in date.split('-')])
        else:
            # by default, report relative to today
            # determine date 100 years earlier
            relative_date = datetime.date.today() - relativedelta(years=100)

        return relative_date

    def find_events(self, date):
        '''Find events 100 years before the current day or
        a specified day in YYYY-MM-DD format.'''

        # find all events for this date
        # exclude partially known dates
        # - purchase date precision == start date precision
        # (borrow end *could* have different precision than start date)
        events = Event.objects \
            .filter(Q(start_date=date) |
                    Q(subscription__purchase_date=date) |
                    Q(borrow__isnull=False, end_date=date)) \
            .filter(Q(start_date_precision__isnull=True) |
                    Q(start_date_precision=int(self.full_precision)))
        return events

    def report(self, date):
        # needs two modes:
        # - schedule
        # - tweet (takes event id)
        for ev in self.find_events(date):
            print('event type %s' % ev.event_type)
            print('account %s' % ev.account)
            print(ev)
            content = tweet_content(ev, date)
            print(content)

    # times:  9 AM, 12 PM, 1:30 PM, 3 PM, 4:30 PM, 6 PM, 8 PM
    tweet_times = ['9:00', '12:00', '13:30', '15:00', '16:30', '18:00',
                   '20:00']

    def schedule(self, date):
        # find all events for today
        self.find_events(date)
        # filter out any that can't be tweeted
        events = [ev for ev in self.find_events(date) if can_tweet(ev, date)]

        # schedule the ones that can be tweeted
        for i, ev in enumerate(events):
            self.tweet_at(ev, self.tweet_times[i])

    def tweet_at(self, event, time):
        '''schedule a tweet for later today'''
        cmd = '%s %s/manage.py twitterbot_100years tweet --event %s' % \
            (sys.executable, settings.PROJECT_ROOT, event.id)
        print('scheduling %s at %s' % (event, time))
        print(cmd)
        result = subprocess.run(['/usr/bin/at', time], input=cmd.encode(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stderr.decode())

    def tweet(self, event, date):
        # make sure the event is tweetable
        if not can_tweet(event, date):
            return

        content = tweet_content(event, date)
        if not content:
            return
        print(content)
        # TODO: set credentials in local settings
        # auth = tweepy.OAuthHandler('', '')
        # auth.set_access_token('', '')
        # api = tweepy.API(auth)
        # api.update_status(content)


tweetable_event_types = ['Subscription', 'Renewal', 'Reimbursement',
                         'Borrow', 'Purchase', 'Request']


def can_tweet(ev, date):
    '''check if the event can be tweeted on the specified day'''

    # convert to string and compare against partial dates
    # to ensure we don't tweet an event with an unknown date
    date = date.isoformat()

    # disallows subscription on start date != purchase
    if ev.event_label == 'Subscription' and \
       ev.subscription.partial_purchase_date != date:
        return False

    return any([
        # subscription event and date matches purchase
        (ev.event_label == 'Subscription' and
         ev.subscription.partial_purchase_date == date),
        # borrow event and date matches end date
        (ev.event_label == 'Borrow' and ev.partial_end_date == date),
        # any other tweetable event and date matches start
        ev.event_label in tweetable_event_types and
        ev.partial_start_date == date])


def tweet_content(ev, event_date):
    # handle multiple members, but use first member for url
    member = ev.account.persons.first()

    if isinstance(event_date, str):
        try:
            event_date = datetime.date(*[int(n) for n in event_date.split('-')])
        except TypeError:
            # given a partial date
            return

    member_name = ' and '.join(m.name for m in ev.account.persons.all())
    prolog = '#100YearsAgoToday on %s:' % \
        event_date.strftime(Command.date_format)
    content = None

    event_label = ev.event_label

    if event_label == 'Subscription' and \
       ev.subscription.purchase_date == event_date:
        content = '%s joined the Shakespeare and Company lending library.' % \
            member_name

    elif event_label in ['Borrow', 'Purchase', 'Request']:
        work = work_label(ev.work)
        # convert event type into verb for the sentence
        verb = '%sed' % ev.event_type.lower().rstrip('e')
        if event_label == 'Borrow' and ev.end_date == event_date:
            verb = 'returned'
        content = '%s %s %s.' % (member_name, verb, work)

    # renewal
    elif event_label == 'Renewal' and ev.subscription.purchase_date == event_date:
        # renewed for 2 months at 1 volume per month
        content = '%s renewed for %s' % \
            (member_name, ev.subscription.readable_duration())
        # include volume count if known
        if ev.subscription.volumes:
            content = '%s at %d volume%s per month.' % \
                (content, ev.subscription.volumes,
                 '' if ev.subscription.volumes == 1 else 's')

    elif event_label == 'Reimbursement':
        # renewed for 2 months at 1 volume per month
        content = '%s received a reimbursement for %s%s from the Shakespeare and Company lending library' % \
            (member_name, ev.reimbursement.refund,
             ev.reimbursement.currency_symbol())

    # any other kind of event: no tweet

    if content:
        # change: use card detail url if possible
        url = card_url(member, ev) or member.get_absolute_url()
        return '%s %s\n%s' % (prolog, content, absolutize_url(url))


def work_label(work):
    # convert work to twitter display format:
    # - standard: author\'s "title" (year)
    # - periodical: an issue of "title"
    parts = []
    # indicate issue of periodical based on format
    if work.format() == 'Periodical':
        # TODO: include actual issue if known?
        parts.append('an issue of')

    if work.authors:
        # TODO: handle multiple authors
        # two: Francis Beaumont and John Fletcher's "Plays."
        # more than (3?): Francis Beaument et al.'s "title"'
        parts.append('%s’s' % work.authors[0].name)

    # TODO: include editor if there are no authors, e.g.
    # "Book of Gardening," edited by John Smith (DATE)

    # should always have title; use quotes since we can't italicize
    # strip quotes if already present (uncertain title)
    parts.append('“%s”' % work.title.strip('"“”'))

    # include work year if known not before 1500
    if work.year and work.year > 1500:
        parts.append('(%s)' % work.year)

    return ' '.join(parts)


def card_url(member, ev):
    footnote = None

    if ev.event_footnotes.exists():
        footnote = ev.event_footnotes.first()

    if not footnote and ev.event_type == 'Borrow' and \
       ev.borrow.footnotes.exists():
        footnote = ev.borrow.footnotes.first()

    if not footnote and ev.event_type == 'Purchase' and \
       ev.purchase.footnotes.exists():
        footnote = ev.purchase.footnotes.first()

    if footnote and footnote.image:
        url = reverse('people:member-card-detail', kwargs={
                      'slug': member.slug,
                      'short_id': footnote.image.short_id})
        return '%s#e%d' % (url, ev.id)
