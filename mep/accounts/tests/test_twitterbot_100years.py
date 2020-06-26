from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from mep.accounts.models import Event
from mep.accounts.management.commands import twitterbot_100years
from mep.books.models import Creator, CreatorType, Work
from mep.people.models import Person


class TestTwitterBot100years(TestCase):

    def setUp(self):
        self.cmd = twitterbot_100years.Command()
        self.cmd.stdout = StringIO()

    # def test_command_line(self):
    #     # test calling via command line with args
    #     stdout = StringIO()
    #     call_command('report_timegaps', csvtempfile.name, stdout=stdout)


class TestWorkLabel(TestCase):
    fixtures = ['sample_works']

    def test_authors(self):
        # - standard format: author's "title" (year), but handle multiple

        # no author, no year
        blue_train = Work.objects.get(pk=5)
        assert twitterbot_100years.work_label(blue_train) == \
            '“Murder on the Blue Train”'

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
        exit_eliza = Work.objects.get(pk=1)
        exit_eliza.year = 1350
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain’s “Exit Eliza”"

    def test_periodical(self):
        the_dial = Work.objects.get(pk=4598)
        assert twitterbot_100years.work_label(the_dial) == \
            "an issue of “The Dial”"


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
        assert 'joined the Shakespeare and Company lending library'  \
            in tweet
