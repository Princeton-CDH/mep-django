from io import StringIO

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.core.management import call_command

from mep.accounts.management.commands import report_timegaps
from mep.accounts.models import Account


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
