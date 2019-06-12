import datetime

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
import pytest

from mep.accounts.partial_date import DatePrecision

## migration test case adapted from
# https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
# and from winthrop-django


class TestMigrations(TransactionTestCase):

    # @property
    # def app(self):
    #     return apps.get_containing_app_config(type(self).__module__).name
    app = None
    migrate_from = None
    migrate_to = None

    def setUp(self):
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass


# NOTE: TransactionTestCase must be run after all other test cases,
# because it truncates the database, removing fixture objects expected
# to be present by other tests.
# Django test runner runs transaction test cases after simple test cases,
# but pytest / pytest-django do not.
@pytest.mark.last
class TestTempPrecisionEvent(TestMigrations):

    app = 'accounts'
    migrate_from = '0027_address_partial_dates'
    migrate_to = '0028_temp_precision_event'
    serialized_rollback = True

    def setUpBeforeMigration(self, apps):

        Account = apps.get_model('accounts', 'Account')
        Borrow = apps.get_model('accounts', 'Borrow')
        Purchase = apps.get_model('accounts', 'Purchase')

        # Account to hold events
        account = Account.objects.create()


        # Create some objects with partial dates
        Borrow.objects.create(
                account=account,
                start_date=datetime.date(1950, 1, 5),
                end_date=datetime.date(1950, 1, 6),
                start_date_precision=DatePrecision.year,
                end_date_precision=DatePrecision.month
        )
        Borrow.objects.create(
                account=account,
                start_date=datetime.date(1900, 2, 10),
                end_date=datetime.date(1900, 2, 12),
                start_date_precision=DatePrecision.day | DatePrecision.month
        )

        Purchase.objects.create(
            account=account,
            start_date=datetime.date(1950, 1, 5),
            end_date=datetime.date(1950, 1, 6),
            start_date_precision=DatePrecision.year,
            end_date_precision=DatePrecision.month
        )
        Purchase.objects.create(
            account=account,
            start_date=datetime.date(1900, 2, 10),
            end_date=datetime.date(1900, 2, 12),
            start_date_precision=DatePrecision.day | DatePrecision.month
        )

        # Create some that don't have partial dates
        Borrow.objects.create(
            account=account,
            start_date=datetime.date(1955, 1, 5),
            end_date=datetime.date(1955, 1, 8),
        )
        Purchase.objects.create(
            account=account,
            start_date=datetime.date(1957, 2, 10),
            end_date=datetime.date(1957, 2, 12)
        )

    def test_copy_precisions(self):

        Event = self.apps.get_model('accounts', 'Event')

        for event in Event.objects.all():
            # get the borrow or the purchase off of the Event
            borrow_or_purchase = getattr(event, 'borrow', None)
            if borrow_or_purchase is None:
                borrow_or_purchase = getattr(event, 'purchase')
            # check that regardless of state, the precisions
            # were copied over as expected
            assert event.temp_start_date_precision == \
                borrow_or_purchase.start_date_precision
            assert event.temp_end_date_precision == \
                borrow_or_purchase.end_date_precision

