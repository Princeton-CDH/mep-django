import codecs
import csv
from typing import Dict

from django.core.management.base import BaseCommand
import pymarc

from mep.books.models import Item
from mep.books.oclc import SRUSearch, oclc_uri, get_work_uri


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

    def handle(self, *args, **kwargs):
        """Loop through Items in the database and look for matches in OCLC"""
        self.sru_search = SRUSearch()

        # filter out items with problems that we don't expect to be
        # able to match reliably
        items = Item.objects.exclude(notes__contains='GENERIC') \
                            .exclude(notes__contains='PROBLEM') \
                            .exclude(notes__contains='OBSCURE') \
                            .exclude(title__endswith='*')

        with open('items-oclc.csv', 'w') as csvfile:
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

    def oclc_search(self, item: Item) -> Dict:
        """Search for an item in OCLC by title, author, date.
        Returns dictionary with details found for inclusion in CSV.
        """
        # get local instance of sru_search to add filters to
        sru_search = self.sru_search.filter()

        if item.title:
            sru_search = sru_search.filter(title__exact='"%s"' % item.title)

        if item.authors.exists():
            sru_search = sru_search.filter(author__all='"%s"' % item.authors.first())

        if item.year:
            sru_search = sru_search.filter(year=item.year)
        else:
            first_date = item.first_known_interaction
            if first_date:
                # range search ending with first known event date
                sru_search = sru_search.filter(year="-%s" % first_date.year)

        result = sru_search.search()
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
                'Work URI': get_work_uri(marc_record)
            })
        return oclc_info
