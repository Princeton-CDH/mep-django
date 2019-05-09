import codecs
from collections import defaultdict
import csv

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
import progressbar
import pymarc

from mep.books.models import Item
from mep.books.oclc import SRUSearch, WorldCatEntity


class Command(BaseCommand):
    """Associate library items with OCLC entries via WordCat Search API"""
    help = __doc__

    mode = None
    sru_search = None

    #: fields to be included in CSV export
    csv_fieldnames = [
        # details from local db
        'Title', 'Date', 'Creators',
        # details from OCLC
        'OCLC Title', 'OCLC Author', 'OCLC Date', 'OCLC URI',
        'Work URI', '# matches',
        # db notes last
        'Notes']

    #: summary message string for each mode
    summary_message = {
        'report': 'Processed %(count)d items, found matches for %(found)d',
        'update': 'Processed %(count)d items, updated %(updated)d',
    }

    progbar = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = defaultdict(int)

        self.script_user = User.objects.get(username=settings.SCRIPT_USERNAME)
        self.item_content_type = ContentType.objects.get_for_model(Item).pk

    def add_arguments(self, parser):
        parser.add_argument('mode', choices=['report', 'update'])
        parser.add_argument(
            '--no-progress', action='store_true',
            help='Do not display progress bar')
        parser.add_argument(
            '-o', '--output', help='Filename for the report to be generated')

    def handle(self, *args, **kwargs):
        """Loop through Items in the database and look for matches in OCLC"""

        # store operating mode
        self.mode = kwargs['mode']
        # initialize OCLC search client
        self.sru_search = SRUSearch()

        # filter out items with problems that we don't expect to be
        # able to match reliably
        # only include items that do not already have a work URI
        items = Item.objects.exclude(notes__contains='GENERIC') \
                            .exclude(notes__contains='PROBLEM') \
                            .exclude(notes__contains='OBSCURE') \
                            .exclude(notes__contains='ZERO') \
                            .filter(uri__exact='') \
                            .exclude(title__endswith='*')

        # report on total to process
        total = items.count()
        self.stdout.write('%d items to reconcile' % total)

        # bail out if there is nothing to do
        if not total:
            return

        if not kwargs['no_progress'] and total > 5:
            self.progbar = progressbar.ProgressBar(redirect_stdout=True,
                                                   max_value=total)
        if self.mode == 'report':
            # use output name specified in args, with a default fallback
            outfilename = kwargs.get('output', None) or 'items-oclc.csv'
            self.report(items, outfilename)
        elif self.mode == 'update':
            self.update_items(items)

        if self.progbar:
            self.progbar.finish()

        # summarize what was done for the current mode
        self.stdout.write(self.summary_message[self.mode] % self.stats)

    def tick(self):
        '''Increase count by one and update progress bar if there is one'''
        self.stats['count'] += 1
        if self.progbar:
            self.progbar.update(self.stats['count'])

    def report(self, items, outfilename):
        '''Generate an CSV file to report on OCLC matches found'''
        with open(outfilename, 'w') as csvfile:
            # write utf-8 byte order mark at the beginning of the file
            csvfile.write(codecs.BOM_UTF8.decode())
            # initialize csv writer
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_fieldnames)
            writer.writeheader()

            for item in items:
                info = {
                    'Title': item.title,
                    'Date': item.year,
                    'Creators': ';'.join([str(person) for person in item.creators.all()]),
                    'Notes': item.notes
                }
                info.update(self.oclc_info(item))
                writer.writerow(info)
                # keep track of how many records found any matches
                if info.get('# matches', None):
                    self.stats['found'] += 1

                self.tick()

    def update_items(self, items):
        '''Search for Items in OCLC and update in the database if
        a match is found.'''
        for item in items:
            worldcat_entity = self.oclc_search_record(item)
            if worldcat_entity:
                item.populate_from_worldcat(worldcat_entity)
                item.save()
                # create log entry to document the change
                LogEntry.objects.log_action(
                    user_id=self.script_user.id,
                    content_type_id=self.item_content_type,
                    object_id=item.pk,
                    object_repr=str(item),
                    change_message='Updated from OCLC %s' % worldcat_entity.item_uri,
                    action_flag=CHANGE)

                self.stats['updated'] += 1

            self.tick()

    def oclc_search(self, item):
        """Search for an item in OCLC by title, author, date, and
        material type if noted as a Periodical. Returns
        :class:`~mep.books.oclc.SRWResponse`.
        """
        search_opts = {}

        # search by title if known
        if item.title:
            search_opts['title__exact'] = item.title

        # search by first author if there is one
        if item.authors.exists():
            search_opts['author__all'] = str(item.authors.first())

        # search by year if known
        if item.year:
            search_opts['year'] = item.year
        # search year by range based on first documented event for this book
        else:
            first_date = item.first_known_interaction
            if first_date:
                # range search ending with first known event date
                search_opts['year'] = "-%s" % first_date.year

        # filter by material type; assume item is a book unless
        # notes indicate periodical
        search_opts['material_type__exact'] = 'periodical' \
            if 'PERIODICAL' in item.notes else 'book'

        return self.sru_search.search(**search_opts)

    def oclc_info(self, item):
        """Search for an item in OCLC by title, author, date.
        Returns dictionary with details found for inclusion in CSV.
        """
        result = self.oclc_search(item)
        # report number of matches so 0 is explicit/obvious
        oclc_info = {'# matches': result.num_records}
        if result.num_records:
            # assume first record is best match (seems to be true)
            marc_record = result.marc_records[0]
            worldcat_rdf = self.sru_search.get_worldcat_rdf(marc_record)
            oclc_info.update({
                'OCLC Title': marc_record.title(),
                'OCLC Author': marc_record.author(),
                'OCLC Date': marc_record.pubyear(),
                'OCLC URI': worldcat_rdf.item_uri,
                'Work URI': worldcat_rdf.work_uri
            })
        return oclc_info

    def oclc_search_record(self, item: Item) -> WorldCatEntity:
        """Search for an item in OCLC by title, author, date.
        Returns :class:`~mep.books.oclc.WorldCatResource` for the first
        match.'''
        """
        result = self.oclc_search(item)
        if result and result.num_records:
            return self.sru_search.get_worldcat_rdf(result.marc_records[0])
