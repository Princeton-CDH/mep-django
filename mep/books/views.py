from dal import autocomplete
from django.db.models import Q
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin

from mep.books.forms import WorkSearchForm
from mep.books.models import Work
from mep.books.queryset import WorkSolrQuerySet
from mep.common import SCHEMA_ORG
from mep.common.utils import absolutize_url
from mep.common.views import AjaxTemplateMixin, FacetJSONMixin, \
    LabeledPagesMixin, LoginRequiredOr404Mixin, RdfViewMixin


class WorkList(LoginRequiredOr404Mixin, LabeledPagesMixin, ListView,
               FormMixin, AjaxTemplateMixin, FacetJSONMixin, RdfViewMixin):
    '''List page for searching and browsing library items.'''
    model = Work
    page_title = "Books"
    page_description = "Search and browse books by title and filter " + \
        "by bibliographic metadata."
    template_name = 'books/work_list.html'
    ajax_template_name = 'books/snippets/work_results.html'
    paginate_by = 100
    context_object_name = 'works'
    rdf_type = SCHEMA_ORG.SearchResultPage

    form_class = WorkSearchForm
    _form = None
    initial = {'sort': 'title'}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        form_data = self.request.GET.copy()

        # always use relevance sort for keyword search;
        # otherwise use default (sort by title)
        if form_data.get('query', None):
            form_data['sort'] = 'relevance'
        else:
            form_data['sort'] = self.initial['sort']

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
        'title': 'sort_title_isort',
    }

    #: bib data query alias field syntax (type defaults to edismax in solr config)
    search_bib_query = '{!qf=$bib_qf pf=$bib_pf v=$bib_query}'

    def get_queryset(self):
        # NOTE faceting so that response doesn't register as an error;
        # data is currently unused
        sqs = WorkSolrQuerySet().facet_field('format', exclude='format')

        form = self.get_form()

        # empty qs if not valid
        if not form.is_valid():
            sqs = sqs.none()

        # otherwise apply filters, query, sort, etc.
        else:
            search_opts = form.cleaned_data

            if search_opts.get('query', None):
                sqs = sqs.search(self.search_bib_query) \
                         .raw_query_parameters(bib_query=search_opts['query']) \
                         .also('score')  # include relevance score in results

            sqs = sqs.order_by(self.solr_sort[search_opts['sort']])

        self.queryset = sqs
        return sqs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        facets = self.object_list.get_facets().get('facet_fields', None)
        error_message = ''
        # facets are not set if there is an error on the query
        if facets:
            self._form.set_choices_from_facets(facets)
        else:
            # if facets are not set, the query errored
            error_message = 'Something went wrong.'

        context.update({
            'page_title': self.page_title,
            'page_description': self.page_description,
            'error_message': error_message
        })
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
            (self.page_title, self.get_absolute_url())
        ]


class WorkDetail(LoginRequiredOr404Mixin, DetailView, RdfViewMixin):
    '''Detail page for a single library book.'''
    model = Work
    template_name = 'books/work_detail.html'
    context_object_name = 'work'
    rdf_type = SCHEMA_ORG.ItemPage

    def get_absolute_url(self):
        '''Get the full URI of this page.'''
        return absolutize_url(self.object.get_absolute_url())

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        return [
            ('Home', absolutize_url('/')),
            (WorkList.page_title, WorkList().get_absolute_url()),
            (self.object.title, self.get_absolute_url())
        ]

class WorkAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.books.models.Work` for borrowing and purchasing events'''

    def get_queryset(self):
        '''Get a queryset filtered by query string. Only
        searches on title, mep id and notes for now, since that is all
        our stub records include.
        '''
        return Work.objects.filter(
            Q(title__icontains=self.q) |
            Q(mep_id__icontains=self.q) |
            Q(notes__icontains=self.q)
        ).order_by('title')    # meaningful default sort?
