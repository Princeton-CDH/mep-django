"""
Manage.py command to import logbooks from MEP XML. Example usage::

    python manage.py import_logbooks /path/to/logbooks/

Accounts are created for any existing or new people not already imported
into the personography. Any new people are also created with a stub entry that
can later be manually expanded.

See :meth:`mep.accounts.xml_models.XmlEvent.to_db_event` for detailed info
on the import process.
"""
import glob
import logging
import os
from django.core.management.base import BaseCommand, CommandError
from mep.accounts.xml_models import LogBook
from mep.accounts.models import Account, Event, Subscribe, Reimbursement

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Import logbooks from XML documents"""
    help = __doc__

    def add_arguments(self, parser):

        parser.add_argument('path',
            help='path to folder containting XML logbooks')

    def get_totals(self):
        return {
            'events': Event.objects.count(),
            'subscriptions': Subscribe.objects.count(),
            'renewals': Subscribe.objects.filter(modification='ren').count(),
            'reimbursements': Reimbursement.objects.count(),
            'supplements': Subscribe.objects.filter(modification='sup').count()
        }

    def summarize(self, start_totals):
        final_totals = self.get_totals()
        for i in ['people', 'addresses', 'countries', 'urls']:
            self.stdout.write('%d %s added (%d total)\n' %
                (new_totals[i] - start_totals[i], i, new_totals[i]))

    def get_file_list(self, path):
        """Get filenames of any xml in Logbook dir"""
        if not os.path.isdir(path):
            raise CommandError('Please provide a path to the XML logbooks. '
                               'Path provided looks like a file.')
        file_list = glob.glob(path + '*.xml')
        if not file_list:
            raise CommandError('There are no XML files in the provided path.')
        return file_list

    def handle(self, *args, **kwargs):
        files = self.get_file_list(kwargs['path'])
        totals = self.get_totals()
        for f in files:
            log = LogBook.from_file(f)
            if log and isinstance(log, LogBook):
                for day in log.days:
                    for event in day.events:
                        try:
                            event.to_db_event(day.date)
                        except Exception as err:
                            self.stdout.write(
                                self.style.WARNING(
                                    '%s, on %s date' % (err, day.date)
                                )
                            )
        self.summarize(totals)
