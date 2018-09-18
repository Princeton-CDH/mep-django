import codecs
from datetime import date, timedelta
from io import StringIO
from tempfile import NamedTemporaryFile

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
        # test calling via command line with args
        csvtempfile = NamedTemporaryFile(suffix='csv')
        stdout = StringIO()
        call_command('report_timegaps', csvtempfile.name, stdout=stdout)

        output = stdout.getvalue()
        # no accounts, nothing done
        assert 'Examining 0 accounts with at least two events' in output
        # check that summarize is called
        assert 'Found 0 accounts with gaps larger than 6 months' in output

        # alternate gap size honored
        stdout = StringIO()
        call_command('report_timegaps', csvtempfile.name, gap=12, stdout=stdout)
        output = stdout.getvalue()
        assert 'Found 0 accounts with gaps larger than 1 year' in output

        csvtempfile.seek(0)
        csv_content = csvtempfile.read().decode()
        assert csv_content.startswith(codecs.BOM_UTF8.decode())
        assert ','.join(self.cmd.csv_header) in csv_content

        # create account and events
        account = Account.objects.create()
        Event.objects.create(
            account=account, start_date=date(1943, 1, 1),
            end_date=date(1943, 2, 1))
        Event.objects.create(
            account=account, start_date=date(1963, 3, 1),
            end_date=date(1943, 4, 1))
        call_command('report_timegaps', csvtempfile.name, stdout=stdout)
        csvtempfile.seek(0)
        csv_content = csvtempfile.read().decode()
        # account number/person name included in report
        assert str(account) in csv_content
        # account summary dates included
        assert account.earliest_date().isoformat() in csv_content
        assert account.last_date().isoformat() in csv_content
        # generate gap and report to check inclusion in csv
        gaps = self.cmd.find_gaps(account, timedelta(days=30 * 6))
        max_gap, msg = self.cmd.report_gap_details(gaps)
        # number of gaps, max gap in days, detail all included
        assert str(len(gaps)) in csv_content
        assert str(max_gap) in csv_content
        assert msg in csv_content

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
            account=account, start_date=date(1943, 1, 1),
            end_date=date(1943, 2, 1))
        event2 = Event.objects.create(
            account=account, start_date=date(1943, 3, 1),
            end_date=date(1943, 4, 1))
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
        start_date = date(1922, 1, 1)
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
            account=account, start_date=date(1943, 1, 1),
            end_date=date(1943, 2, 1))
        borrow = Borrow.objects.create(account=account)
        borrow.partial_start_date = '1950-01'
        borrow.save()
        # gap is significant, but partial dates are skipped
        assert self.cmd.find_gaps(account, timedelta(days=61)) == []

    def test_report_gap_details(self):
        # shouldn't be called with empty gap list normally, but shouldn't error
        max_gap, msg = self.cmd.report_gap_details([])
        assert max_gap == 0
        assert msg == ''

        account = Account.objects.create()
        # add two events to check simple case of gap and message
        event1 = Event.objects.create(
            account=account, start_date=date(1943, 1, 1),
            end_date=date(1943, 2, 1))
        delta_days = 20
        event2 = Event.objects.create(
            account=account, start_date=event1.end_date + timedelta(days=delta_days))
        max_gap, msg = self.cmd.report_gap_details([(event1, event2)])
        # largest gap reported in days
        assert max_gap == delta_days
        # message includes days and event type
        # (generic events currently display as just 'generic', but there are very few)
        assert msg == '{} days between {}/{} Generic and {}/?? Generic'.format(
            delta_days, event1.start_date.isoformat(), event1.end_date.isoformat(),
            event2.start_date.isoformat()
        )

        # if multiple events, largest gap is returned
        delta2_days = 25
        event3 = Event.objects.create(
            account=account, start_date=event2.start_date + timedelta(days=delta2_days))
        max_gap, msg = self.cmd.report_gap_details([(event1, event2), (event2, event3)])
        assert max_gap == delta2_days
        # message reports on both gaps
        assert '{} days between'.format(delta_days) in msg
        assert '{} days between'.format(delta2_days) in msg

        # event type should be reported in message
        borrow = Borrow.objects.create(account=account)
        borrow.partial_start_date = (event3.start_date + timedelta(days=30)).isoformat()
        max_gap, msg = self.cmd.report_gap_details([(event3, borrow)])
        assert '{}/?? Borrow'.format(borrow.partial_start_date) in msg




