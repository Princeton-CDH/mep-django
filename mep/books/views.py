from dal import autocomplete
from django.db.models import Q
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin

from mep.books.forms import ItemSearchForm
from mep.books.models import Item
from mep.books.queryset import ItemSolrQuerySet
from mep.common import SCHEMA_ORG
from mep.common.utils import absolutize_url
from mep.common.views import (AjaxTemplateMixin, FacetJSONMixin,
                              LabeledPagesMixin, RdfViewMixin)


class ItemList(LabeledPagesMixin, ListView, FormMixin, AjaxTemplateMixin, FacetJSONMixin, RdfViewMixin):
    '''List page for searching and browsing library items.'''
    model = Item
    template_name = 'books/item_list.html'
    ajax_template_name = 'books/snippets/item_results.html'
    paginate_by = 100
    context_object_name = 'items'
    rdf_type = SCHEMA_ORG.SearchResultPage

    form_class = ItemSearchForm
    _form = None
    initial = {'sort': 'title'}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        form_data = self.request.GET.copy()

        # set defaults
        for key, val in self.initial.items():
            form_data.setdefault(key, val)

        kwargs['data'] = form_data
        return kwargs

    def get_form(self, *args, **kwargs):
        if not self._form:
            self._form = super().get_form(*args, **kwargs)
        return self._form

    # map form sort to solr sort
    solr_sort = {
        'relevance': '-score',
        'title': 'title_s',
    }

    def get_queryset(self):
        # NOTE faceting on pub date currently as a placeholder; no UI use yet
        sqs = ItemSolrQuerySet().facet_field('pub_date_i')
        form = self.get_form()

        # empty qs if not valid
        if not form.is_valid():
            sqs = sqs.none()
        # otherwise apply filters, query, sort, etc.
        else:
            search_opts = form.cleaned_data
            sqs = sqs.order_by(self.solr_sort[search_opts['sort']])

        self.queryset = sqs
        return sqs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self._form.set_choices_from_facets(
            self.object_list.get_facets()['facet_fields'])
        return context

    def get_page_labels(self, paginator):
        '''generate labels for pagination'''
        form = self.get_form()
        # if invalid, should show 'N/A'
        if not form.is_valid():
            return [(1, 'N/A')]

        # otherwise default to numbered pages for now
        # NOTE could implement alpha here, but tougher for titles
        return super().get_page_labels(paginator)

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
