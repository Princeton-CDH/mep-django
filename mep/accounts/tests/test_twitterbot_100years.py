from datetime import date
from io import StringIO

from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
import pytest

from mep.accounts.models import Event
from mep.accounts.management.commands import twitterbot_100years
from mep.accounts.templatetags import mep_100years_tags
from mep.books.models import Creator, CreatorType, Work
from mep.people.models import Person


class TestTwitterBot100years(TestCase):
    fixtures = ['test_events']

    def setUp(self):
        self.cmd = twitterbot_100years.Command()
        self.cmd.stdout = StringIO()

    # def test_command_line(self):
    #     # test calling via command line with args
    #     stdout = StringIO()
    #     call_command('report_timegaps', csvtempfile.name, stdout=stdout)

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
        print('borrow end date %s' % borrow.end_date)
        # FIXME: ???
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
