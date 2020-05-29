import datetime

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
import pytest

from mep.accounts.partial_date import DatePrecision

# migration test case adapted from
# https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
# and from winthrop-django


@pytest.mark.last
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
    def check_copy_precisions(old_values, model):
        '''Test that a Model and its pre-migration/reversion values were
        copied over as expected.'''
        for pk, start_precision, end_precision in old_values:
            mymodel = model.objects.get(pk=pk)
            # these precisions should be the same, regardless of whether Event
            # or one of its subclasses holds the field
            assert mymodel.start_date_precision == start_precision
            assert mymodel.end_date_precision == end_precision


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


@pytest.mark.last
class TestSubscriptionPurchaseDateAdjustments(TestMigrations):

    app = 'accounts'
    migrate_from = '0032_subscription_add_purchase_date'
    migrate_to = '0033_subscription_purchase_date_adjustments'

    def setUpBeforeMigration(self, apps):
        Account = apps.get_model('accounts', 'Account')
        Subscription = apps.get_model('accounts', 'Subscription')

        # Account to hold events
        account = Account.objects.create()
        # subscription with two renewals that overlap previous dates
        self.sub = Subscription.objects.create(
            account=account,
            start_date=datetime.date(1920, 4, 30),
            end_date=datetime.date(1920, 7, 30),
        )
        self.renew1 = Subscription.objects.create(
            account=account,
            start_date=datetime.date(1920, 7, 27),
            end_date=datetime.date(1920, 10, 27),
            subtype='ren'
        )
        self.renew2 = Subscription.objects.create(
            account=account,
            start_date=datetime.date(1920, 10, 26),
            end_date=datetime.date(1921, 4, 26),
            subtype='ren'
        )
        # third renewal with no overlap
        self.renew3 = Subscription.objects.create(
            account=account,
            start_date=datetime.date(1921, 6, 1),
            end_date=datetime.date(1921, 8, 1),
            subtype='ren'
        )

        # renewal with no preceding subscription
        account2 = Account.objects.create()
        self.account2_renew = Subscription.objects.create(
            account=account2,
            start_date=datetime.date(1920, 7, 27),
            end_date=datetime.date(1920, 10, 27),
            subtype='ren'
        )

        # renewal with preceding subscription but no end date
        account3 = Account.objects.create()
        self.account3_sub = Subscription.objects.create(
            account=account3,
            start_date=datetime.date(1920, 4, 30),
        )
        self.account3_renew = Subscription.objects.create(
            account=account3,
            start_date=datetime.date(1920, 7, 27),
            end_date=datetime.date(1920, 10, 27),
            subtype='ren'
        )

        # increment by months and not days
        account4 = Account.objects.create()
        self.account4_sub = Subscription.objects.create(
            account=account4,
            start_date=datetime.date(1920, 5, 1),
            end_date=datetime.date(1920, 6, 1),
        )
        self.account4_renew = Subscription.objects.create(
            account=account4,
            start_date=datetime.date(1920, 5, 25),
            end_date=datetime.date(1920, 6, 25),
            # not explicitly a renewal
        )
        self.account4_renew2 = Subscription.objects.create(
            account=account4,
            start_date=datetime.date(1920, 6, 22),
            end_date=datetime.date(1920, 7, 22),
        )

    def test_adjust_subscriptions(self):
        Subscription = self.apps.get_model('accounts', 'Subscription')
        sub = Subscription.objects.get(pk=self.sub.pk)
        # subscription purchase date should be set from start date
        assert sub.purchase_date == self.sub.start_date
        assert sub.purchase_date_precision == self.sub.start_date_precision

        # first renewal should start after the first subscription ends
        renew1 = Subscription.objects.get(pk=self.renew1.pk)
        # purchase date set from old start date
        assert renew1.purchase_date == self.renew1.start_date
        # renewal starts same day subscription ends
        assert renew1.start_date == datetime.date(1920, 7, 30)
        # renewal has same duration, end date adjusted
        assert renew1.end_date == datetime.date(1920, 10, 30)

        # second renewal should start after *adjusted* first renewal
        renew2 = Subscription.objects.get(pk=self.renew2.pk)
        # purchase date set from original start date
        assert renew2.purchase_date == self.renew2.start_date
        # renewal starts same day as adusted renewal end date
        assert renew2.start_date == datetime.date(1920, 10, 30)
        # same duration, end date adjusted
        assert renew2.end_date == datetime.date(1921, 4, 30)

        # third renewal should not be adjusted
        renew3 = Subscription.objects.get(pk=self.renew3.pk)
        # purchase date set from original start date
        assert renew3.purchase_date == self.renew3.start_date
        # start date and end date unchanged
        assert renew3.start_date == self.renew3.start_date
        assert renew3.end_date == self.renew3.end_date

        # renewal with no preceding subscription should not change
        account2_renew = Subscription.objects.get(pk=self.account2_renew.pk)
        assert account2_renew.purchase_date == self.account2_renew.start_date
        assert account2_renew.start_date == self.account2_renew.start_date
        assert account2_renew.end_date == self.account2_renew.end_date

        # renewal with preceding subscription with noend date should not change
        account3_renew = Subscription.objects.get(pk=self.account3_renew.pk)
        assert account3_renew.purchase_date == self.account3_renew.start_date
        assert account3_renew.start_date == self.account3_renew.start_date
        assert account3_renew.end_date == self.account3_renew.end_date

        # renewal with preceding subscription with noend date should not change
        account4_renew = Subscription.objects.get(pk=self.account4_renew.pk)
        assert account4_renew.purchase_date == self.account4_renew.start_date
        assert account4_renew.start_date == self.account4_sub.end_date
        assert account4_renew.end_date == datetime.date(1920, 7, 1)
        account4_renew2 = Subscription.objects.get(pk=self.account4_renew2.pk)
        assert account4_renew2.purchase_date == self.account4_renew2.start_date
        assert account4_renew2.start_date == account4_renew.end_date
        assert account4_renew2.end_date == datetime.date(1920, 8, 1)
