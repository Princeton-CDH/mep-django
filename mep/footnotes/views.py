
from dal import autocomplete
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from mep.common import SCHEMA_ORG
from mep.common.utils import absolutize_url, alpha_pagelabels
from mep.common.views import AjaxTemplateMixin, FacetJSONMixin, \
    LabeledPagesMixin, LoginRequiredOr404Mixin, RdfViewMixin
from mep.footnotes.forms import CardSearchForm
from mep.footnotes.models import Bibliography
from mep.footnotes.queryset import CardSolrQuerySet


class BibliographyAutocomplete(autocomplete.Select2QuerySetView):
    '''Autocomplete for :class:`mep.footnotes.models.Bibliography` for use
    with django-autocomplete-light in the purchase change view.'''

    def get_queryset(self):
        '''Get a queryset filtered by query string.
        Filters on
        :attr:`~mep.footnotes.models.Bibliography.bibliographic_note`.
        '''
        return Bibliography.objects \
            .filter(bibliographic_note__icontains=self.q)


class CardList(LoginRequiredOr404Mixin, LabeledPagesMixin, ListView,
               FormMixin, AjaxTemplateMixin, FacetJSONMixin, RdfViewMixin):
    '''List page for searching and browsing lending cards.'''
    model = Bibliography
    template_name = 'footnotes/card_list.html'
    ajax_template_name = 'footnotes/snippets/card_results.html'
    paginate_by = 30
    context_object_name = 'cards'
    rdf_type = SCHEMA_ORG.SearchResultPage

    form_class = CardSearchForm
    # cached form instance for current request
    _form = None
    #: initial form values
    initial = {
        'sort': 'name'
    }
    # map form sort to solr sort field
    solr_sort = {
        'relevance': '-score',
        'name': 'cardholder_sort'
    }

    #: mappings for Solr field names to form aliases
    range_field_map = {
        'account_years': 'membership_dates',
    }
    #: fields to generate stats on in self.get_ranges
    stats_fields = ('card_years')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # use GET instead of default POST/PUT for form data
        form_data = self.request.GET.copy()

        # always use relevance sort for keyword search;
        # otherwise use default (sort by name)
        # if form_data.get('query', None):
            # form_data['sort'] = 'relevance'
        # else:
        form_data['sort'] = self.initial['sort']

        # use initial values as defaults
        for key, val in self.initial.items():
            form_data.setdefault(key, val)

        kwargs['data'] = form_data

        # get min/max configuration for range fields
        # kwargs['range_minmax'] = self.get_range_stats()

        return kwargs

    def get_queryset(self):
        sqs = CardSolrQuerySet()
        form = self.get_form()

        # empty queryset if not valid
        if not form.is_valid():
            sqs = sqs.none()

        # when form is valid, check for search term and filter queryset
        else:
            search_opts = form.cleaned_data

        # order based on solr name for search option
        sqs = sqs.order_by(self.solr_sort[search_opts['sort']])

        self.queryset = sqs
        return self.queryset

    def get_page_labels(self, paginator):
        '''generate labels for pagination'''

        # if form is invalid, page labels should show 'N/A'
        form = self.get_form()
        if not form.is_valid():
            return [(1, 'N/A')]

        # no keyword search for now
        # when sorting by relevance, use default page label logic
        # if form.cleaned_data['sort'] == 'relevance':
        #    return super().get_page_labels(paginator)

        # otherwise, when sorting by alpha, generate alpha page labels
        pagination_qs = self.queryset.only('cardholder_sort')
        alpha_labels = alpha_pagelabels(paginator, pagination_qs,
                                        lambda x: x['cardholder_sort'])
        # alpha labels is a dict; use items to return list of tuples
        return alpha_labels.items()

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        return [
            ('Home', absolutize_url('/')),
            ('Cards', self.get_absolute_url()),
        ]

    def get_absolute_url(self):
        '''Get the full URI of this page.'''
        return absolutize_url(reverse('footnotes:cards-list'))
