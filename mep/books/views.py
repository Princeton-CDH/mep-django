import csv
from io import StringIO

from dal import autocomplete
from django.db.models import Q
from django.http import StreamingHttpResponse
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import ListView

from mep.books.models import Item


class ItemAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.books.models.Item` for borrowing and purchasing events'''

    def get_queryset(self):
        '''Get a queryset filtered by query string. Only
        searches on title, mep id and notes for now, since that is all
        our stub records include.
        '''
        return Item.objects.filter(
            Q(title__icontains=self.q) |
            Q(mep_id__icontains=self.q) |
            Q(notes__icontains=self.q)
        ).order_by('title')    # meaningful default sort?



class ItemCSV(ListView):
    '''Export of item details as CSV download.'''
    # NOTE: adapted from PPA: could be extracted as a view mixin for reuse
    model = Item
    # order by id for now, for simplicity
    ordering = 'id'
    header_row = ['Admin link', 'Database ID', 'Title', 'Year', 'URI',
                  'Authors', 'MEP ID', 'Notes']
    # NOTE: omitting editors and translators because it's slow enough
    # already with just authors

    def get_csv_filename(self):
        return 'mep-items-%s.csv' % now().strftime('%Y%m%dT%H:%M:%S')

    def get_data(self):
        # generator of rows of data for inclusion in CSV download
        yield self.header_row
        # # NOTE: prefetch creators in an effort to rerieve them more efficiently
        for item in self.get_queryset().prefetch_related('creator_set'):
            yield (reverse('admin:books_item_change', args=[item.id]),
                    item.id, item.title, item.year, item.uri,
                    ';'.join([str(auth) for auth in item.authors]),
                    item.mep_id, item.notes)

        # all at once, rather than one at a time for each item

    def render_to_csv(self, data):

        # pesudo buffer class per django docs
        # https://docs.djangoproject.com/en/1.11/howto/outputting-csv/#streaming-csv-files
        class Echo:
            """An object that implements just the write method of the file-like
            interface.
            """
            def write(self, value):
                """Write the value by returning it, instead of storing in a buffer."""
                return value

        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        # writer.writerow(self.header_row)

        response = StreamingHttpResponse(
            (writer.writerow(row) for row in self.get_data()),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
            self.get_csv_filename()

        return response

    def get(self, *args, **kwargs):
        return self.render_to_csv(self.get_data())