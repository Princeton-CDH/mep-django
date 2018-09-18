from io import StringIO
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.core.management import call_command

from mep.accounts.management.commands import report_timegaps
from mep.accounts.models import Account, Event, Borrow


class TestReportTimegaps(TestCase):

    def setUp(self):
        self.cmd = report_timegaps.Command()
        self.cmd.stdout = StringIO()

    # @patch('mep.people.management.commands.import_personography.Personography')
    def test_command_line(self):
        # TODO
        # test calling via command line with args
        pass

    def test_format_relativedelta(self):
        assert self.cmd.format_relativedelta(relativedelta(years=1)) == '1 year'
        assert self.cmd.format_relativedelta(relativedelta(years=2)) == '2 years'
        assert self.cmd.format_relativedelta(relativedelta(years=2, months=3)) \
            == '2 years, 3 months'
        assert self.cmd.format_relativedelta(relativedelta(years=2, months=1)) \
             == '2 years, 1 month'
        assert self.cmd.format_relativedelta(relativedelta(years=2, months=1)) \
            == '2 years, 1 month'
        assert self.cmd.format_relativedelta(relativedelta(years=5, days=1)) \
            == '5 years, 1 day'
        assert self.cmd.format_relativedelta(relativedelta(years=6, days=10)) \
            == '6 years, 10 days'
        assert self.cmd.format_relativedelta(relativedelta(years=6, months=2, days=10)) \
            == '6 years, 2 months, 10 days'

    def test_find_gaps(self):
        account = Account.objects.create()

        # no dates, no gaps
        assert self.cmd.find_gaps(account, timedelta(days=30)) == []

        # two events close together, smaller than the gap = still no gaps
        event1 = Event.objects.create(
            account=account, start_date=datetime(1943, 1, 1),
            end_date=datetime(1943, 2, 1))
        event2 = Event.objects.create(
            account=account, start_date=datetime(1943, 3, 1),
            end_date=datetime(1943, 4, 1))
        assert self.cmd.find_gaps(account, timedelta(days=30)) == []

        # if first event end date is not found, start date should be used
        # with gap size of 30 days, this is a gap (1/1 - 3/1)
        event1.end_date = None
        event1.save()
        gaps = self.cmd.find_gaps(account, timedelta(days=30))
        # 1 gap found, returns start/end event objects for the gap
        assert len(gaps) == 1
        assert gaps[0] == (event1, event2)
        # with larger gap size, no gaps should be found
        assert self.cmd.find_gaps(account, timedelta(days=90)) == []

        # if second event start date is not found, end date should be used
        event2.start_date = None
        # 1/1 - 4/1 should be a gap at 30 days
        gaps = self.cmd.find_gaps(account, timedelta(days=30))
        assert len(gaps) == 1
        assert gaps[0] == (event1, event2)

        account.event_set.all().delete()

        # multiple events + gaps
        start_date = datetime(1922, 1, 1)
        # create multiple objects; start and end date 30 days apart,
        # next event 30 days after previous end
        for i in range(5):
            Event.objects.create(account=account, start_date=start_date,
                                 end_date=start_date + timedelta(days=30))
            start_date += timedelta(days=60)

        # no gaps when gapsize is larger than 30
        assert self.cmd.find_gaps(account, timedelta(days=31)) == []
        # 4 gaps when gapsize is less
        gaps = self.cmd.find_gaps(account, timedelta(days=29))
        assert len(gaps) == 4
        events = account.event_set.all()
        assert gaps[0] == (events[0], events[1])
        assert gaps[3] == (events[3], events[4])

        # borrow events with partial dates are currently ignored
        account.event_set.all().delete()
        Event.objects.create(
            account=account, start_date=datetime(1943, 1, 1),
            end_date=datetime(1943, 2, 1))
        borrow = Borrow.objects.create(account=account)
        borrow.partial_start_date = '1950-01'
        borrow.save()
        # gap is significant, but partial dates are skipped
        assert self.cmd.find_gaps(account, timedelta(days=61)) == []

