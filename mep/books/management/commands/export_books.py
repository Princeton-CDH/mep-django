'''
Manage command to export book data for use by others.

Generates a CSV and JSON file including details on every book in the
database, with bibliographic details and counts for all events, borrows,
and purchases.

'''

from collections import OrderedDict

from django.db.models import F

from mep.books.models import CreatorType, Work
from mep.common.management.export import BaseExport
from mep.common.utils import absolutize_url


class Command(BaseExport):
    '''Export book data.'''
    help = __doc__

    model = Work

    # get a current list of creator types from the database
    # - only include types with creators associated
    creator_types = CreatorType.objects.all().filter(creator__isnull=False) \
                               .distinct() \
                               .values_list('name', flat=True)
    # NOTE: might want to move csv fields this into a method so we don't
    # query the database at load time (but maybe only a problem for tests)

    csv_fields = ['uri', 'title'] + \
        [creator.lower() for creator in creator_types] + [
        "year",
        "format",
        "identified",
        "work uri",
        "edition uri",
        "ebook url",
        "volumes/issues",
        "notes",
        "event count",
        "borrow count",
        "purchase count",
        "updated"
    ]

    def get_base_filename(self):
        '''use "books" instead of "works" for export file'''
        return 'books'

    def get_queryset(self):
        '''Retrieve all books, with creators prefetched and annotations
        for event counts to make the export more efficient; sort by year
        (missing last) and then title.'''
        return super().get_queryset().prefetch_related('creator_set') \
                      .count_events() \
                      .order_by(F('year').asc(nulls_last=True), 'title')

    def get_object_data(self, work):
        '''
        Generate dictionary of data to export for a single
        :class:`~mep.books.models.Work`
        '''
        # required properties
        data = OrderedDict([
            ('uri', absolutize_url(work.get_absolute_url())),
            ('title', work.title),
        ])
        data.update(self.creator_info(work))
        if work.year:
            data['year'] = work.year
        # format is not currently set for all items
        if work.work_format:
            data['format'] = work.work_format.name

        # identified: true unless work is marked as uncertain
        data['identified'] = not work.is_uncertain

        if work.uri:
            data['work uri'] = work.uri
        if work.edition_uri:
            data['edition uri'] = work.edition_uri
        if work.ebook_url:
            data['ebook url'] = work.ebook_url
        # text listing of volumes/issues
        if work.edition_set.exists():
            data['volumes/issues'] = [vol.display_text() for vol in
                                      work.edition_set.all()]
        # public notes
        if work.public_notes:
            data['notes'] = work.public_notes

        # always include event counts
        data['event count'] = work.event_count
        data['borrow count'] = work.borrow_count
        data['purchase count'] = work.purchase_count
        # date last modified
        data['updated'] = work.updated_at.isoformat()

        return data

    def creator_info(self, work):
        '''Add information about authors, editors, etc based on creators
        associated with this work.'''
        info = OrderedDict()
        for creator_type in self.creator_types:
            creators = work.creator_by_type(creator_type)
            if creators:
                info[creator_type.lower()] = [c.sort_name for c in creators]
        return info
