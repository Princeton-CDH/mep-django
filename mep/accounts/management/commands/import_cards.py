from collections import defaultdict
import glob
import os.path

from django.core.management.base import BaseCommand
from eulxml import xmlmap

from mep.accounts.models import Account
from mep.accounts.xml_models import LendingCard
from mep.people.models import Person


class Command(BaseCommand):
    """Import lending card data from XML documents"""
    help = __doc__

    v_normal = 1

    def add_arguments(self, parser):

        parser.add_argument('path',
            help='base path containing folders of lending card XML files')

    def handle(self, *args, **kwargs):
        search_path = os.path.join(kwargs['path'], '**', '*.xml')
        verbosity = kwargs['verbosity']

        cardfiles = glob.iglob(search_path, recursive=True)

        stats = defaultdict(int)

        for i, card_file in enumerate(cardfiles):
            stats['files'] += 1
            lcard = xmlmap.load_xmlobject_from_file(card_file, LendingCard)
            # output file name, cardholders, and number of borrowing events
            # when running in verbose mode
            cardholders = ', '.join(['%s %s' % (cardholder.mep_id, cardholder.name)
                                     for cardholder in lcard.cardholders])
            if verbosity > self.v_normal:
                self.stdout.write('%s: %s' % (card_file, cardholders))
                self.stdout.write('%d borrowing events' % len(lcard.borrowing_events))
            stats['card_holders'] += len(lcard.cardholders)
            stats['borrow_events'] += len(lcard.borrowing_events)

            # find the account associated with the cardholder
            # (or all carholders, if there are multiple)
            accounts = Account.objects.all()
            for cardholder in lcard.cardholders:
                accounts = accounts.filter(persons__mep_id=cardholder.mep_id)

            if accounts.exists():
                account = accounts.first()
                stats['accounts'] += 1
            else:
                # TODO: create account
                # - get person record for each card holder
                # - create account associated with all card holders

                # Temporarily skipping for now
                self.stdout.write(self.style.WARNING('Account not found for %s\n%s' \
                    % (cardholders, card_file)))
                stats['skipped'] += 1
                continue

            # iterate through borrowing events and associate with the acount
            for xml_borrow in lcard.borrowing_events:
                try:
                    xml_borrow.to_db_event(account).save()
                    stats['borrow_created'] += 1
                except ValueError as verr:
                    # TODO: handle partial dates
                    # (skip for now)
                    print(verr)

            # skip after processing max number
            # NOTE: could add configurable max records option for testing
            # if i > 30:
                # break

        # summarize what was done
        self.stdout.write('''\nSummary:
{files:,} files processed
{card_holders:,} card holders
{accounts:,} accounts
{borrow_events:,} borrowing events found
{borrow_created:,} borrowing events created
{skipped:,} files skipped
'''.format(**stats))
