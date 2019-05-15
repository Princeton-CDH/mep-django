from dal import autocomplete
from django.db.models import Q
from django.views.generic import ListView
from django.urls import reverse

from mep.books.models import Item
from mep.books.queryset import ItemSolrQuerySet
from mep.common.views import LabeledPagesMixin, RdfViewMixin
from mep.common.utils import absolutize_url


class ItemList(LabeledPagesMixin, ListView, RdfViewMixin):
    '''List page for searching and browsing library items.'''
    model = Item
    template_name = 'books/item_list.html'
    paginate_by = 100
    context_object_name = 'items'

    def get_queryset(self):
        return ItemSolrQuerySet().order_by('title')

    def get_uri(self):
        return absolutize_url(reverse('books:books-list'))

    def get_breadcrumbs(self):
        return [
            ('Home', absolutize_url('/')),
            ('Books', self.get_uri())
        ]


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
