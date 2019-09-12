import datetime

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
import pytest

from mep.accounts.partial_date import DatePrecision

# migration test case adapted from
# https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
# and from winthrop-django


class TestMigrations(TransactionTestCase):

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


class DatePrecisionCopies(TestMigrations):

    app = 'accounts'

    def setUpBeforeMigration(self, apps):

        Account = apps.get_model('accounts', 'Account')
        Borrow = apps.get_model('accounts', 'Borrow')
        Purchase = apps.get_model('accounts', 'Purchase')
        Subscription = apps.get_model('accounts', 'Subscription')

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

        # Subscription just to check that non-partial date items function as
        # expected
        Subscription.objects.create(
            account=account,
            start_date=datetime.date(1958, 2, 1),
            end_date=datetime.date(1958, 2, 8)
        )

        # force data to serialize to list and not lazily evaluate
        # after migration when testing
        self.old_borrows = list(Borrow.objects.values_list(
            'pk', 'start_date_precision', 'end_date_precision'
        ))
        self.old_purchases = list(Purchase.objects.values_list(
            'pk', 'start_date_precision', 'end_date_precision'
        ))

    @staticmethod
    def check_copy_precisions(old_values, Model):
        '''Test that a Model and its pre-migration/reversion values were
        copied over as expected.'''
        for tup in old_values:
            model = Model.objects.get(pk=tup[0])
            # these precisions should be the same, regardless of whether Event
            # or one of its subclasses holds the field
            assert model.start_date_precision == tup[1]
            assert model.end_date_precision == tup[2]


# NOTE: TransactionTestCase must be run after all other test cases,
# because it truncates the database, removing fixture objects expected
# to be present by other tests.
# Django test runner runs transaction test cases after simple test cases,
# but pytest / pytest-django do not.
@pytest.mark.second_to_last
class TestCopyPrecisions(DatePrecisionCopies):

    migrate_from = '0027_address_partial_dates'
    migrate_to = '0028_generic_event_partial_dates'

    def test_copy_precisions(self):

        Event = self.apps.get_model('accounts', 'Event')
        Borrow = self.apps.get_model('accounts', 'Borrow')
        Purchase = self.apps.get_model('accounts', 'Purchase')
        Subscription = self.apps.get_model('accounts', 'Subscription')

        # event object now has date precicions
        event = Event.objects.first()
        assert hasattr(event, 'start_date_precision')
        assert hasattr(event, 'end_date_precision')

        # Also check subscription to make sure it has None for
        # precisions as expected.
        subscription = Subscription.objects.first()
        assert subscription.start_date_precision is None
        assert subscription.end_date_precision is None

        # check that precisions were copied correctly on Borrow
        # and purchase
        self.check_copy_precisions(self.old_borrows, Borrow)
        self.check_copy_precisions(self.old_purchases, Purchase)


@pytest.mark.last
class TestRevertPrecisionCopy(DatePrecisionCopies):
    migrate_from = '0028_generic_event_partial_dates'
    migrate_to = '0027_address_partial_dates'

    def test_revert_precision_copy(self):

        Event = self.apps.get_model('accounts', 'Event')
        Borrow = self.apps.get_model('accounts', 'Borrow')
        Purchase = self.apps.get_model('accounts', 'Purchase')
        Subscription = self.apps.get_model('accounts', 'Subscription')

        # event object DOES NOT have date precicions as one of its fields
        event = Event.objects.first()
        assert not hasattr(event, 'start_date_precision')
        assert not hasattr(event, 'end_date_precision')

        # neither does Subscriptions
        subscription = Subscription.objects.first()
        assert not hasattr(subscription, 'start_date_precision')
        assert not hasattr(subscription, 'end_date_precision')

        # check that precisions were copied correctly on Borrow
        # and purchase
        self.check_copy_precisions(self.old_borrows, Borrow)
        self.check_copy_precisions(self.old_purchases, Purchase)
