import sys
import uuid
from collections import OrderedDict
from datetime import date
from io import StringIO
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
import pytest

from mep.accounts.models import Event
from mep.accounts.management.commands import twitterbot_100years
from mep.accounts.templatetags import mep_100years_tags
from mep.accounts.views import Twitter100yearsReview
from mep.books.models import Creator, CreatorType, Work
from mep.people.models import Person


class TestTwitterBot100years(TestCase):
    fixtures = ['test_events']

    def setUp(self):
        self.cmd = twitterbot_100years.Command()
        self.cmd.stdout = StringIO()

    def test_command_line(self):
        # test calling via command line with args
        stdout = StringIO()
        reimb = Event.objects.filter(reimbursement__isnull=False,
                                     start_date__isnull=False).first()
        call_command('twitterbot_100years', 'report', '-d',
                     reimb.partial_start_date, stdout=stdout)
        output = stdout.getvalue()
        assert 'Event id: %s' % reimb.pk in output
        assert tweet_content(reimb, reimb.start_date) in output

        # get the date 100 years ago
        day = self.cmd.get_date()

        # call schedule
        with patch.object(twitterbot_100years.Command,
                          'schedule') as mock_schedule:
            call_command('twitterbot_100years', 'schedule')
            assert mock_schedule.call_count == 1
            mock_schedule.assert_called_with(day)

        # call tweet
        with patch.object(twitterbot_100years.Command,
                          'tweet') as mock_tweet:
            # call with valid id
            call_command('twitterbot_100years', 'tweet', '-e', reimb.pk)
            assert mock_tweet.call_count == 1
            mock_tweet.assert_called_with(reimb, day)

            # call with invalid id
            with pytest.raises(CommandError):
                call_command('twitterbot_100years', 'tweet', '-e', 'foo')

    def test_get_date(self):
        # by default, date is relative to today
        reldate = date.today() - relativedelta(years=100)
        assert self.cmd.get_date() == reldate
        # date ignored if mode is not report
        assert self.cmd.get_date(date='1920-05-03') == reldate
        # use date specified
        assert self.cmd.get_date(date='1920-05-03', mode='report') \
            == date(1920, 5, 3)
        with pytest.raises(CommandError):
            self.cmd.get_date(date='1920-05', mode='report')

    def test_find_events(self):
        borrow = Event.objects.filter(borrow__isnull=False).first()
        # borrow — both start date and end date
        assert borrow in self.cmd.find_events(borrow.start_date)
        assert borrow in self.cmd.find_events(borrow.end_date)
        # borrows of uncertain items excluded
        borrow2 = Event.objects.filter(borrow__isnull=False).last()
        work = borrow2.work
        work.notes = 'UNCERTAINTYICON'
        work.save()
        assert borrow2 not in self.cmd.find_events(borrow2.start_date)

        subs = Event.objects.filter(subscription__isnull=False,
                                    start_date__isnull=False).first()
        subs.subscription.partial_purchase_date = subs.partial_start_date
        subs.save()
        # start/purchase date
        assert subs in self.cmd.find_events(subs.subscription.purchase_date)
        # not included based on end date
        assert subs not in self.cmd.find_events(subs.end_date)
        # different purchase date
        subs_sub = subs.subscription
        subs_sub.partial_purchase_date = '1936-11-15'
        subs_sub.save()
        assert subs in self.cmd.find_events(subs_sub.purchase_date)

    def test_report(self):
        reimb = Event.objects.filter(reimbursement__isnull=False,
                                     start_date__isnull=False).first()
        self.cmd.report(date=reimb.start_date)
        output = self.cmd.stdout.getvalue()
        assert 'Event id: %s' % reimb.pk in output
        assert tweet_content(reimb, reimb.start_date) in output

    @patch.object(twitterbot_100years.Command, 'tweet_at')
    @patch.object(twitterbot_100years.Command, 'find_events')
    @patch('mep.accounts.management.commands.twitterbot_100years.can_tweet')
    def test_schedule(self, mock_can_tweet, mock_find_events, mock_tweet_at):
        borrow = Event.objects.filter(borrow__isnull=False).first()
        borrow2 = Event.objects.filter(borrow__isnull=False).last()
        subs = Event.objects.filter(subscription__isnull=False,
                                    start_date__isnull=False).first()
        # mock to return multiple to test filtering & scheduling
        mock_find_events.return_value = [borrow, borrow2, subs]
        # can tweet first and last but not second
        mock_can_tweet.side_effect = (True, False, True)
        self.cmd.schedule(borrow.start_date)
        assert mock_tweet_at.call_count == 2
        mock_tweet_at.assert_any_call(borrow, self.cmd.tweet_times[0])
        mock_tweet_at.assert_any_call(subs, self.cmd.tweet_times[1])

    @patch('mep.accounts.management.commands.twitterbot_100years.subprocess')
    def test_tweet_at(self, mock_subprocess):
        event = Event.objects.filter(start_date__isnull=False).first()
        self.cmd.tweet_at(event, '9:00')
        assert mock_subprocess.run.call_count == 1
        args, kwargs = mock_subprocess.run.call_args
        # sanity check subprocess call
        assert args[0][0] == '/usr/bin/at'
        assert args[0][1] == '9:00'
        command = kwargs['input'].decode()
        assert command.startswith('bin/cron-wrapper')
        assert sys.executable in command
        assert command.endswith(
            'manage.py twitterbot_100years tweet --event %d' % event.pk)

    @patch.object(twitterbot_100years.Command, 'get_tweepy')
    @patch('mep.accounts.management.commands.twitterbot_100years.tweet_content')
    def test_tweet(self, mock_tweet_content, mock_get_tweepy):
        reimb = Event.objects.filter(reimbursement__isnull=False,
                                     start_date__isnull=False).first()
        mock_tweet_content.return_value = 'something'
        self.cmd.tweet(reimb, date.today())
        # can tweet is false, not tweeted
        assert mock_get_tweepy.call_count == 0

        # can tweet but no tweet content
        mock_tweet_content.return_value = None
        self.cmd.tweet(reimb, reimb.start_date)
        assert mock_get_tweepy.call_count == 0

        # simulate successful tweet
        mock_tweet_content.return_value = 'something'
        self.cmd.tweet(reimb, reimb.start_date)
        assert mock_get_tweepy.call_count == 1
        mock_api = mock_get_tweepy.return_value
        mock_api.update_status.assert_called_with('something')

    @patch('mep.accounts.management.commands.twitterbot_100years.tweepy')
    def test_get_tweepy(self, mock_tweepy):
        # error if not configured
        with override_settings(TWITTER_100YEARS=None):
            with pytest.raises(CommandError):
                self.cmd.get_tweepy()

            assert mock_tweepy.OAuthHandler.call_count == 0

        api_key = uuid.uuid4()
        api_secret = uuid.uuid4()
        access_token = uuid.uuid4()
        access_secret = uuid.uuid4()
        mock_config = {
            'API': {
                'key': api_key,
                'secret_key': api_secret
            },
            'ACCESS': {
                'token': access_token,
                'secret': access_secret
            }
        }

        with override_settings(TWITTER_100YEARS=mock_config):
            self.cmd.get_tweepy()
            mock_tweepy.OAuthHandler.assert_called_with(api_key, api_secret)
            auth = mock_tweepy.OAuthHandler.return_value
            auth.set_access_token.assert_called_with(access_token,
                                                     access_secret)
            mock_tweepy.API.assert_called_with(auth)


class TestWorkLabel(TestCase):
    fixtures = ['sample_works']

    def test_authors(self):
        # - standard format: author's "title" (year), but handle multiple

        # no author, no year
        blue_train = Work.objects.get(pk=5)
        assert twitterbot_100years.work_label(blue_train) == \
            '“Murder on the Blue Train.”'

        # single author with years
        exit_eliza = Work.objects.get(pk=1)
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain’s “Exit Eliza” (1912)"

        # add second author
        auth2 = Person.objects.create(name='Lara Cain', sort_name='Cain, Lara',
                                      slug='cain')
        author = CreatorType.objects.get(name='Author')
        Creator.objects.create(person=auth2, work=exit_eliza,
                               creator_type=author, order=2)
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain and Lara Cain’s “Exit Eliza” (1912)"

        # add third author
        auth3 = Person.objects.create(name='Mary Fain', sort_name='Fain, Mary',
                                      slug='fain')
        Creator.objects.create(person=auth3, work=exit_eliza,
                               creator_type=author, order=3)
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain et al.’s “Exit Eliza” (1912)"

    def test_editors(self):
        # editors listed if no author but editors

        # get work with no author
        blue_train = Work.objects.get(pk=5)

        # add editor
        ed1 = Person.objects.create(name='Lara Cain', sort_name='Cain, Lara',
                                    slug='cain')
        editor = CreatorType.objects.get(name='Editor')
        Creator.objects.create(person=ed1, work=blue_train,
                               creator_type=editor, order=1)
        assert twitterbot_100years.work_label(blue_train) == \
            "“Murder on the Blue Train,” edited by Lara Cain"
        # add second editor
        ed2 = Person.objects.create(name='Mara Vain', sort_name='Vain, Mara',
                                    slug='vain')
        Creator.objects.create(person=ed2, work=blue_train,
                               creator_type=editor, order=2)
        assert twitterbot_100years.work_label(blue_train) == \
            "“Murder on the Blue Train,” edited by Lara Cain and Mara Vain"
        # third editor
        ed3 = Person.objects.create(name='Nara Wain', sort_name='Wain, Nara',
                                    slug='wain')
        Creator.objects.create(person=ed3, work=blue_train,
                               creator_type=editor, order=3)
        assert twitterbot_100years.work_label(blue_train) == \
            "“Murder on the Blue Train,” edited by Lara Cain et al."

    def test_year(self):
        # set pre-modern publication date  — should not be included
        # - should include period inside quotes
        exit_eliza = Work.objects.get(pk=1)
        exit_eliza.year = 1350
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain’s “Exit Eliza.”"

    def test_periodical(self):
        the_dial = Work.objects.get(pk=4598)
        assert twitterbot_100years.work_label(the_dial) == \
            "an issue of “The Dial.”"


class TestCanTweet(TestCase):
    fixtures = ['test_events']

    def test_reimbursement(self):
        reimb = Event.objects.filter(reimbursement__isnull=False,
                                     start_date__isnull=False).first()
        assert twitterbot_100years.can_tweet(reimb, reimb.start_date)
        assert not twitterbot_100years.can_tweet(reimb, date.today())

    def test_borrow(self):
        # borrow with fully known start and end date
        borrow = Event.objects.filter(
            borrow__isnull=False, start_date__isnull=False,
            end_date__isnull=False, start_date_precision=7).first()
        # can tweet on start date
        assert twitterbot_100years.can_tweet(borrow, borrow.start_date)
        # can tweet on end date
        assert twitterbot_100years.can_tweet(borrow, borrow.end_date)
        # cannot tweet on other dats
        assert not twitterbot_100years.can_tweet(borrow, date.today())

        # borrow with partially known date
        borrow = Event.objects.filter(start_date_precision=6).first()
        # cannot tweet on any date
        assert not twitterbot_100years.can_tweet(borrow, borrow.start_date)

    def test_purchase(self):
        purchase = Event.objects.filter(purchase__isnull=False).first()
        assert twitterbot_100years.can_tweet(purchase, purchase.start_date)
        assert not twitterbot_100years.can_tweet(purchase, date.today())

    def test_subscription(self):
        # regular subscription with precisely known dates
        subs = Event.objects.get(pk=8810)
        # purchase date same as start date
        subs.subscription.purchase_date = subs.start_date
        assert twitterbot_100years.can_tweet(subs, subs.start_date)
        assert not twitterbot_100years.can_tweet(subs, subs.end_date)
        # purchase date different from start date - can't tweet on start
        subs.subscription.purchase_date = subs.end_date
        assert not twitterbot_100years.can_tweet(subs, subs.start_date)


class TestCardUrl(TestCase):
    fixtures = ['test_events']

    def test_card_url(self):
        ev = Event.objects.filter(footnotes__isnull=False).first()
        member = ev.account.persons.first()
        assert twitterbot_100years.card_url(member, ev) == \
            '%s#e%d' % (
                reverse('people:member-card-detail', kwargs={
                        'slug': member.slug,
                        'short_id': ev.footnotes.first().image.short_id}),
                ev.id)

        ev = Event.objects.filter(footnotes__isnull=True).first()
        assert not twitterbot_100years.card_url(member, ev)


tweet_content = twitterbot_100years.tweet_content


class TestTweetContent(TestCase):
    fixtures = ['test_events']

    def test_reimbursement(self):
        reimb = Event.objects.filter(reimbursement__isnull=False,
                                     start_date__isnull=False).first()
        tweet = tweet_content(reimb, reimb.partial_start_date)
        assert reimb.start_date \
            .strftime(twitterbot_100years.Command.date_format) in tweet
        assert reimb.account.persons.first().name in tweet
        refund = 'received a reimbursement for %s%s' % \
            (reimb.reimbursement.refund,
             reimb.reimbursement.currency_symbol())
        assert refund in tweet
        assert reimb.account.persons.first().get_absolute_url() in tweet

        # partial date = no tweet content
        assert not tweet_content(reimb, reimb.start_date.strftime('%Y'))
        assert not tweet_content(reimb, reimb.start_date.strftime('%Y-%m'))

    def test_borrow(self):
        # borrow with fully known start and end date
        borrow = Event.objects.filter(
            borrow__isnull=False, start_date__isnull=False,
            end_date__isnull=False, start_date_precision=7).first()
        # borrow
        tweet = tweet_content(borrow, borrow.partial_start_date)
        borrowed = '%s borrowed %s' % \
            (borrow.account.persons.first().name,
             twitterbot_100years.work_label(borrow.work))
        assert borrowed in tweet

        # return
        tweet = tweet_content(borrow, borrow.partial_end_date)
        returned = '%s returned %s' % \
            (borrow.account.persons.first().name,
             twitterbot_100years.work_label(borrow.work))
        assert returned in tweet

    def test_subscription(self):
        # regular subscription with precisely known dates
        subs = Event.objects.get(pk=8810)
        # purchase date same as start date
        subs.subscription.purchase_date = subs.start_date
        tweet = tweet_content(subs, subs.partial_start_date)
        assert 'subscribed for 1 month at 2 volumes per month'  \
            in tweet

    def test_tweet_text_tag(self):
        subs = Event.objects.get(pk=8810)
        subs.subscription.purchase_date = subs.start_date
        assert mep_100years_tags.tweet_text(subs, subs.partial_start_date) == \
            tweet_content(subs, subs.partial_start_date)


class TestTwitter100yearsReview(TestCase):
    fixtures = ['test_events']

    def setUp(self):
        self.view = Twitter100yearsReview()

    def test_get_date_range(self):
        start, end = self.view.get_date_range()
        assert start == date.today() - relativedelta(years=100)
        assert end == start + relativedelta(months=3)
        assert self.view.date_start == start
        assert self.view.date_end == end

    def test_get_queryset(self):
        with patch.object(self.view, 'get_date_range') as mock_get_date_range:
            # borrowed on 11/19, returned 11/20
            borrow = Event.objects.get(end_date='1936-11-25')
            mock_get_date_range.return_value = \
                (date(1936, 11, 20), date(1936, 12, 20))
            events = self.view.get_queryset()
            assert len(events) == 1
            # borrow should be included based on end date
            assert borrow in events

            # after/between fixture dates — no events
            mock_get_date_range.return_value = \
                (date(1936, 12, 1), date(1936, 12, 30))
            assert not self.view.get_queryset().exists()

            # uncertain works excluded
            work = borrow.work
            work.notes = 'UNCERTAINTYICON'
            work.save()
            mock_get_date_range.return_value = \
                (date(1936, 11, 20), date(1936, 12, 20))
            assert not self.view.get_queryset().exists()

            # ignore partially known dates
            mock_get_date_range.return_value = \
                (date(1900, 1, 1), date(1900, 2, 1))
            assert not self.view.get_queryset().exists()

    def test_get_context_data(self):
        # borrowed on 11/19, returned 11/20
        borrow = Event.objects.get(end_date='1936-11-25')
        reimb = Event.objects.filter(reimbursement__isnull=False,
                                     start_date__isnull=False).first()
        subs = Event.objects.filter(subscription__isnull=False,
                                    start_date__isnull=False).first()
        # fixture includes a borrow with unknown start but known end
        no_start = Event.objects.filter(start_date__isnull=True,
                                        end_date__isnull=False).first()

        # wide date range for the reimbursement
        self.view.date_start = date(1936, 11, 20)
        self.view.date_end = date(1941, 12, 6)
        self.view.object_list = [borrow, reimb, no_start, subs]

        context = self.view.get_context_data()
        events = context['events_by_date']
        assert isinstance(events, OrderedDict)
        # inspect the dictionary of dates and events
        assert borrow.partial_end_date in events
        print('partial start %s' % reimb.partial_start_date)
        assert reimb.partial_start_date in events
        assert borrow in events[borrow.partial_end_date]
        assert reimb in events[reimb.partial_start_date]
        # borrow start before the range should not be present
        assert borrow.partial_start_date not in events
        # end date on no start is out of range
        assert no_start.partial_end_date not in events
        # no unset keys from unknown dates
        assert None not in events

        # widen the range
        self.view.date_start = date(1936, 1, 1)
        context = self.view.get_context_data()
        events = context['events_by_date']
        # now includes borrow start and no-start borrow end
        assert borrow.partial_start_date in events
        assert no_start.partial_end_date in events
        # still includes others
        assert reimb.partial_start_date in events

    # not currently testing review template
