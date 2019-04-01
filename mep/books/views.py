from dal import autocomplete
from django.db.models import Q
from django.views.generic import ListView

from parasolr.django import SolrQuerySet

from mep.books.models import Item
from mep.common.views import LabeledPagesMixin


class ItemList(LabeledPagesMixin, ListView):
    '''List page for searching and browsing library items.'''
    model = Item
    template_name = 'books/item_list.html'
    paginate_by = 100
    context_object_name = 'items'

    def get_queryset(self):
        sqs = SolrQuerySet().filter(item_type='item') \
                            .order_by('title_s') \
                            .only(title='title_s', authors='authors_t',
                                  editors='editors_t', pub_date='pub_date_i',
                                  translators='translators_t', pk='pk_i')
        # NOTE: using only / field limit to alias dynamic field names
        # to something closer to model attribute names
        return sqs


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
