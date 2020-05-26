import datetime

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.urls import reverse

from mep.accounts.models import Event
from mep.accounts.partial_date import DatePrecision
from mep.common.utils import absolutize_url


class Command(BaseCommand):

    # date format:  Saturday, May 8, 1920
    date_format = '%A, %B %-d, %Y'

    full_precision = DatePrecision.year | DatePrecision.month | \
        DatePrecision.day

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--date',
            help='Specify an alternate date in YYYY-MM-DD format (default is today)')

    def handle(self, *args, **kwargs):
        # TODO: arg to get specific day instead of today
        # (or date range for reporting?)
        if kwargs['date']:
            date = datetime.date(*[int(n) for n in kwargs['date'].split('-')])
        else:
            date = datetime.date.today()

        # determine date 100 years earlier
        date = date - relativedelta(years=100)

        # find all events for that date
        # TODO: exclude partially known dates
        events = Event.objects.filter(start_date=date) \
            .filter(Q(start_date_precision__isnull=True) |
                    Q(start_date_precision=int(self.full_precision))) \

        print('%s %d event%s' % (date, events.count(),
                                 's' if events.count() != 1 else ''))

        # TODO: how to group by member?
        # e.g. joined and borrowed
        # test with 2020-05-10 and 2020-05-11

        for ev in events:
            print('event type %s' % ev.event_type)
            print('account %s' % ev.account)
            print(ev)
            content = tweet_content(ev)
            print(content)


def tweet_content(ev):
    # TODO: handle multiple events for the same account on the same day?
    # TODO: handle multiple members
    member = ev.account.persons.first()
    prolog = '#100YearsAgoToday on %s:' % \
        ev.start_date.strftime(Command.date_format)
    content = None

    if ev.event_type == 'Subscription':
        content = '%s joined the Shakespeare and Company lending library.' % \
            member.name

    elif ev.event_type in ['Borrow', 'Purchase']:
        work = work_label(ev.work)
        verb = '%sed' % ev.event_type.lower().rstrip('e')
        content = '%s %s %s.' % (member.name, verb, work)

    # renewal
    elif ev.event_type == 'Renewal':
        # renewed for 2 months at 1 volume per month
        content = '%s renewed for %s' % \
            (member.name, ev.subscription.readable_duration())
        # include volume count if known
        if ev.subscription.volumes:
            content = '%s at %d volume%s per month.' % \
                (content, ev.subscription.volumes,
                 '' if ev.subscription.volumes == 1 else 's')

    # probably don't post these...
    elif ev.event_type == 'Generic':
        print(ev.notes)

    if content:
        # change: use card detail url if possible
        url = card_url(member, ev) or member.get_absolute_url()
        return '%s %s\n%s' % (prolog, content, absolutize_url(url))

    # TODO: add logic to determine schedule and actually schedule
    # tweets for the current day


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
