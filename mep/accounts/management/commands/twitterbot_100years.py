import datetime
import subprocess
import sys

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
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
            # find the event and tweet it, if possible & appropriate
            try:
                ev = Event.objects.get(pk=kwargs['event'])
                self.tweet(ev, date)
            except Event.DoesNotExist:
                self.stderr.write('Error: event %(event)s not found' % kwargs)

    def get_date(self, date=None, mode=None, **kwargs):
        '''Find events relative to the specified day, if set,
        or the date 100 years ago. Overriding the date is only allowed
        in **report** mode.'''

        # only allow overriding date for report
        if date and mode == 'report':
            try:
                relative_date = datetime.date(*[int(n)
                                                for n in date.split('-')])
            except TypeError:
                raise CommandError('Invalid date %s' % date)
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
                    Q(start_date_precision=int(self.full_precision))) \
            .exclude(work__notes__contains="UNCERTAINTYICON")
        return events

    def report(self, date):
        '''Print out the content that would be tweeted on the specified day'''
        for ev in self.find_events(date):
            tweet_text = tweet_content(ev, date)
            if tweet_text:
                self.stdout.write('Event id: %s' % ev.id)
                self.stdout.write(tweet_text)
                self.stdout.write('\n')

    # times:  9 AM, 12 PM, 1:30 PM, 3 PM, 4:30 PM, 6 PM, 8 PM
    tweet_times = ['9:00', '12:00', '13:30', '15:00', '16:30', '18:00',
                   '20:00', '10:15', '11:30', '19:00']

    def schedule(self, date):
        '''Schedule all tweetable events for the specified date.'''
        # find all events for today
        self.find_events(date)
        # filter out any that can't be tweeted
        events = [ev for ev in self.find_events(date) if can_tweet(ev, date)]

        # schedule the ones that can be tweeted
        for i, ev in enumerate(events):
            self.tweet_at(ev, self.tweet_times[i])

    def tweet_at(self, event, time):
        '''schedule a tweet for later today'''
        # use current python executable (within virtualenv)
        cmd = 'bin/cron-wrapper %s %s/manage.py twitterbot_100years tweet --event %s' % \
            (sys.executable, settings.PROJECT_ROOT, event.id)
        # could add debug logging here if there are problems
        subprocess.run(['/usr/bin/at', time], input=cmd.encode(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tweet(self, event, date):
        '''Tweet the content for the event on the specified date.'''
        # make sure the event is tweetable
        if not can_tweet(event, date):
            return
        content = tweet_content(event, date)
        if not content:
            return
        api = self.get_tweepy()
        api.update_status(content)

    def get_tweepy(self):
        '''Initialize tweepy API client based on django settings.'''
        if not getattr(settings, 'TWITTER_100YEARS', None):
            raise CommandError('Configuration for twitter access not found')

        auth = tweepy.OAuthHandler(
            settings.TWITTER_100YEARS['API']['key'],
            settings.TWITTER_100YEARS['API']['secret_key'])
        auth.set_access_token(settings.TWITTER_100YEARS['ACCESS']['token'],
                              settings.TWITTER_100YEARS['ACCESS']['secret'])
        return tweepy.API(auth)

tweetable_event_types = ['Subscription', 'Renewal', 'Reimbursement',
                         'Borrow', 'Purchase', 'Request']


def can_tweet(ev, day):
    '''Check if the event can be tweeted on the specified day'''

    # convert to string and compare against partial dates
    # to ensure we don't tweet an event with an unknown date
    day = day.isoformat()
    # disallows subscription on start date != purchase
    if ev.event_label in ['Subscription', 'Renewal'] and \
       ev.subscription.partial_purchase_date != day:
        return False

    return any([
        # subscription event and date matches purchase
        (ev.event_label in ['Subscription', 'Renewal'] and
         ev.subscription.partial_purchase_date == day),
        # borrow event and date matches end date
        (ev.event_label == 'Borrow' and ev.partial_end_date == day),
        # any other tweetable event and date matches start
        ev.event_label in tweetable_event_types and
        ev.partial_start_date == day])


tweet_format = {
    'verbed': '%(member)s %(verb)s %(work)s%(period)s',
    'subscription': '%(member)s %(verb)s for %(duration)s%(volumes)s.',
    'reimbursement': '%(member)s received a reimbursement for ' +
                     '%(amount)s%(currency)s.',
}


def tweet_content(ev, day):
    '''Generate tweet content for the specified event on the specified
    day.'''

    # handle multiple members, but use first member for url
    member = ev.account.persons.first()

    if isinstance(day, str):
        try:
            day = datetime.date(*[int(n) for n in day.split('-')])
        except TypeError:
            # given a partial date
            return

    # all tweets start the same way
    prolog = '#100YearsAgoToday on %s at Shakespeare and Company, ' % \
        day.strftime(Command.date_format)
    # handle shared accounts
    member_name = ' and '.join(m.firstname_last
                               for m in ev.account.persons.all())
    tweet_info = {
        'member': member_name
    }
    event_label = ev.event_label
    tweet_pattern = None

    if event_label in ['Subscription', 'Renewal'] \
       and ev.subscription.purchase_date == day:
        tweet_pattern = 'subscription'
        verb = 'subscribed' if event_label == 'Subscription' else 'renewed'
        # renewals include duration
        tweet_info.update({
            'verb': verb,
            'duration': ev.subscription.readable_duration(),
            'volumes': ''
        })
        # include volume count if known
        if ev.subscription.volumes:
            tweet_info['volumes'] = ', %d volume%s at a time' % \
                (ev.subscription.volumes,
                 '' if ev.subscription.volumes == 1 else 's')

    elif event_label in ['Borrow', 'Purchase', 'Request']:
        tweet_pattern = 'verbed'
        # convert event label into verb for the sentence
        verb = '%sed' % ev.event_label.lower().rstrip('e')
        if event_label == 'Borrow' and ev.end_date == day:
            verb = 'returned'
        work_text = work_label(ev.work)
        tweet_info.update({
            'verb': verb,
            'work': work_text,
            # don't duplicate period inside quotes when no year
            'period': '' if work_text[-1] == '.' else '.'
        })

    elif event_label == 'Reimbursement':
        # received a reimbursement for $##
        tweet_pattern = 'reimbursement'
        tweet_info.update({
            'amount': ev.reimbursement.refund,
            'currency': ev.reimbursement.currency_symbol()
        })

    # if tweet format is set, generate tweet content
    if tweet_pattern:
        content = tweet_format[tweet_pattern] % tweet_info
        # use card detail url when available
        url = card_url(member, ev) or member.get_absolute_url()
        return '%s%s\n%s' % (prolog, content, absolutize_url(url))


def work_label(work):
    '''Convert a :class:`~mep.accounts.models.Work` for display
    in tweet content. Standard formats:
    - author’s “title” (year)
    - periodical: an issue of “title”

    Handles multiple authors (and for two, et al. for more), includes
    editors if there are no authors. Only include years after 1500.
    '''
    parts = []
    # indicate issue of periodical based on format
    if work.format() == 'Periodical':
        # not including issue details even if known;
        # too much variability in format
        parts.append('an issue of')

    include_editors = False

    # include author if known
    if work.authors:
        # handle multiple authors
        if len(work.authors) <= 2:
            # one or two: join by and
            author = ' and '.join([a.firstname_last for a in work.authors])
        else:
            # more than two: first name et al
            author = '%s et al.' % work.authors[0].firstname_last
        parts.append('%s’s' % author)

    # if no author but editors, we will include editor
    elif work.editors:
        include_editors = True

    # should always have title; use quotes since we can't italicize
    # strip quotes if already present (uncertain title)
    # add comma if we will add an editor; add period if no date
    title_punctuation = ''
    if include_editors:
        title_punctuation = ','
    elif not work.year or work.year < 1500:
        title_punctuation = '.'

    # remove any straight or smart quotes included
    # redact offensive term known to occur in titles
    title = work.title.strip('"“”').replace('Nigger', 'N[-----]')

    parts.append('“%s%s”' % (title, title_punctuation))

    # add editors after title
    if include_editors:
        if len(work.editors) <= 2:
            # one or two: join by and
            editor = ' and '.join([ed.firstname_last for ed in work.editors])
        else:
            # more than two: first name et al
            editor = '%s et al.' % work.editors[0].firstname_last
        parts.append('edited by %s' % editor)

    # include work year if known not before 1500
    if work.year and work.year > 1500:
        parts.append('(%s)' % work.year)

    return ' '.join(parts)


def card_url(member, ev):
    '''Return the member card detail url for the event based on footnote
    image, if present.'''
    footnote = ev.footnotes.first()
    if footnote and footnote.image:
        url = reverse('people:member-card-detail', kwargs={
                      'slug': member.slug,
                      'short_id': footnote.image.short_id})
        return '%s#e%d' % (url, ev.id)
