from dal import autocomplete
from django.db.models import Q
from django.views.generic import DetailView, ListView
from django.urls import reverse

from mep.books.models import Item
from mep.books.queryset import ItemSolrQuerySet
from mep.common.views import LabeledPagesMixin, RdfViewMixin
from mep.common.utils import absolutize_url
from mep.common import SCHEMA_ORG


class ItemList(LabeledPagesMixin, ListView, RdfViewMixin):
    '''List page for searching and browsing library items.'''
    model = Item
    template_name = 'books/item_list.html'
    paginate_by = 100
    context_object_name = 'items'
    rdf_type = SCHEMA_ORG.SearchResultPage

    def get_queryset(self):
        return ItemSolrQuerySet().order_by('title')

    def get_absolute_url(self):
        '''Get the full URI of this page.'''
        return absolutize_url(reverse('books:books-list'))

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        # NOTE we can't set this as an attribute on the view because it calls
        # reverse() via get_absolute_url(), which needs the urlconf to be loaded
        return [
            ('Home', absolutize_url('/')),
            ('Books', self.get_absolute_url())
        ]


class ItemDetail(DetailView):
    '''Detail page for a single library book.'''
    model = Item
    template_name = 'books/item_detail.html'
    context_object_name = 'item'


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
