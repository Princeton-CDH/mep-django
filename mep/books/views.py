from dal import autocomplete
from django.db.models import Q
from django.views.generic import ListView

from mep.books.models import Item


class ItemList(ListView):
    model = Item
    paginate_by = 50
    context_object_name = 'items'

    def get_queryset(self):
        return Item.objects.order_by('?')[:50]


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
