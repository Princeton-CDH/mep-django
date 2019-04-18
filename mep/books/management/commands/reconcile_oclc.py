import codecs
import csv
from typing import Dict

from django.core.management.base import BaseCommand
import progressbar
import pymarc

from mep.books.models import Item
from mep.books.oclc import SRUSearch, oclc_uri


class Command(BaseCommand):
    """Associate library items with OCLC entries via WordCat Search API"""
    help = __doc__

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

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-progress', action='store_true',
            help='Do not display progress bar')
        parser.add_argument(
            '-o', '--output', help='Filename for the report to be generated')

    def handle(self, *args, **kwargs):
        """Loop through Items in the database and look for matches in OCLC"""
        self.sru_search = SRUSearch()

        # filter out items with problems that we don't expect to be
        # able to match reliably
        items = Item.objects.exclude(notes__contains='GENERIC') \
                            .exclude(notes__contains='PROBLEM') \
                            .exclude(notes__contains='OBSCURE') \
                            .exclude(title__endswith='*')[:10]

        # report on total to process
        total = items.count()
        self.stdout.write('%d items to reconcile' % total)

        # bail out if there is nothing to do
        if not total:
            return

        progbar = None
        if not kwargs['no_progress'] and total > 5:
            progbar = progressbar.ProgressBar(redirect_stdout=True,
                                              max_value=total)
        count = found = 0

        # use output name specified in args, with a default fallback
        outfilename = kwargs.get('output', None) or 'items-oclc.csv'

        with open(outfilename, 'w') as csvfile:
            # write utf-8 byte order mark at the beginning of the file
            csvfile.write(codecs.BOM_UTF8.decode())

            writer = csv.DictWriter(csvfile, fieldnames=self.csv_fieldnames)
            writer.writeheader()

            for item in items:
                info = {
                    'Title': item.title,
                    'Date': item.year,
                    'Creators': ';'.join([str(person) for person in item.creators.all()]),
                    'Notes': item.notes
                }
                info.update(self.oclc_search(item))
                writer.writerow(info)
                # keep track of how many records found any matches
                if info.get('# matches', None):
                    found += 1

                count += 1
                if progbar:
                    progbar.update(count)

        if progbar:
            progbar.finish()

        # summarize what was done
        self.stdout.write('Processed %d items, found matches for %d' %
                          (count, found))

    def oclc_search(self, item: Item) -> Dict:
        """Search for an item in OCLC by title, author, date.
        Returns dictionary with details found for inclusion in CSV.
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

        result = self.sru_search.search(**search_opts)
        # report number of matches so 0 is explicit/obvious
        oclc_info = {'# matches': result.num_records}
        if result.num_records:
            # assume first record is best match (seems to be true)
            marc_record = result.marc_records[0]
            oclc_info.update({
                'OCLC Title': marc_record.title(),
                'OCLC Author': marc_record.author(),
                'OCLC Date': marc_record.pubyear(),
                'OCLC URI': oclc_uri(marc_record),
                'Work URI': self.sru_search.get_work_uri(marc_record)
            })
        return oclc_info
