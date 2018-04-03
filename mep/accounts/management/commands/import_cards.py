
import glob
import os.path

from django.core.management.base import BaseCommand
from eulxml import xmlmap

from mep.accounts.xml_models import LendingCard
from mep.people.models import Person


class Command(BaseCommand):
    """Import lending card data from XML documents"""
    help = __doc__

    def add_arguments(self, parser):

        parser.add_argument('path',
            help='base path containing folders of lending card XML files')

    def handle(self, *args, **kwargs):
        search_path = os.path.join(kwargs['path'], '**', '*.xml')

        cardfiles = glob.iglob(search_path, recursive=True)

        for i, card_file in enumerate(cardfiles):
            print(card_file)
            lcard = xmlmap.load_xmlobject_from_file(card_file, LendingCard)
            print('%s %s' % (lcard.cardholder_id, lcard.cardholder))
            print('%d borrowing events' % len(lcard.borrowing_events))
            # find the card holder person record
            card_holder = Person.objects.get(mep_id=lcard.cardholder_id)
            # get the person's library account
            # TODO: create if it doesn't already exist
            # *and* if there are events to import
            account = card_holder.account_set.first()
            print(account)
            # iterate through borrowing events and associate with the acount
            for xml_borrow in lcard.borrowing_events:
                try:
                    xml_borrow.to_db_event(account).save()
                except ValueError as verr:
                    # TODO: handle partial dates
                    # (skip for now)
                    print(verr)

            # for testing, bail out after a limited number of cards
            if i > 5:
                break
