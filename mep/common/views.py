import calendar

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.utils.cache import get_conditional_response, patch_vary_headers
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View
from parasolr.django.queryset import SolrQuerySet
from parasolr.utils import solr_timestamp_to_datetime
import rdflib

from mep.common import SCHEMA_ORG


class LoginRequiredOr404Mixin(LoginRequiredMixin):
    '''Extend :class:`~django.contrib.auth.mixins.LoginRequiredMixin`
    to return a 404 if access is denied, rather than redirecting
    to the login form.'''

    def handle_no_permission(self):
        # if permission is denied, raise a 404
        raise Http404


class LabeledPagesMixin(ContextMixin):
    '''View mixin to add labels for pages to a paginated view's context,
    for use in rendering pagination controls.'''

    def get_page_labels(self, paginator):
        '''Generate labels for pages. Defaults to labeling pages using numeric
        ranges, e.g. `50-100`.'''
        page_labels = []

        # if there's nothing to paginate, just return an empty list
        if paginator.count == 0:
            return page_labels
        for page in paginator.page_range:
            # item count starts at zero, goes up by page size
            page_start = (page - 1) * paginator.per_page
            # final page should end at number of the final item
            page_end = min(page_start + paginator.per_page, paginator.count)
            # first item on page is 1-based index, e.g. 51-100
            page_labels.append((page, '%d – %d' % (page_start + 1, page_end)))

        return page_labels

    def get_context_data(self, **kwargs):
        '''Add generated page labels to the view context.'''
        context = super().get_context_data(**kwargs)
        paginator = context['page_obj'].paginator
        context['page_labels'] = self.get_page_labels(paginator)
        # store paginator and generated labels for use in custom headers
        # on ajax response
        self._paginator = paginator
        self._page_labels = context['page_labels']
        return context

    def dispatch(self, request, *args, **kwargs):
        response = super(LabeledPagesMixin, self).dispatch(request, *args, **kwargs)
        if self.request.is_ajax():
        # NOTE we need to replace the en dashes in alpha pagelabels with a
        # hyphen when requested via ajax because unicode can't be sent via the
        # X-Page-Labels header. this needs to get converted back to an en dash
        # on the client side.
            response['X-Page-Labels'] = '|'.join(
                [label.replace('–', '-') for index, label in self._page_labels])
        return response


class RdfViewMixin(ContextMixin):
    '''View mixin to add an RDF linked data graph to context for use in serializing
    and embedding structured data in templates.'''

    #: default schema.org type for a View
    rdf_type = SCHEMA_ORG.WebPage
    #: breadcrumbs, used to render breadcrumb navigation. they should be a list
    #: of tuples like ('Title', '/url')
    breadcrumbs = []

    def get_context_data(self, *args, **kwargs):
        '''Add generated breadcrumbs and an RDF graph to the view context.'''
        context = super().get_context_data(*args, **kwargs)
        return self.add_rdf_to_context(context)

    def get_context(self, request, *args, **kwargs):
        '''Add generated breadcrumbs and RDF graph to Wagtail page context.'''
        context = super().get_context(request, *args, **kwargs)
        return self.add_rdf_to_context(context)

    def add_rdf_to_context(self, context):
        '''add jsonld and breadcrumb list to context dictionary'''
        context.update({
            'page_jsonld': self.as_rdf().serialize(format='json-ld',
                                                   auto_compact=True).decode(),
            'breadcrumbs': self.get_breadcrumbs()
        })
        return context

    def get_absolute_url(self):
        '''Get a URI for this page to use for making RDF assertions. Note that
        this should return a full absolute path, e.g. with absolutize_url().'''
        raise NotImplementedError

    def as_rdf(self):
        '''Generate an RDF graph representing the page.'''
        # add the root node (this page)
        graph = rdflib.ConjunctiveGraph()
        # explicitly bind schema.org namespace
        graph.bind('schema', SCHEMA_ORG)
        page_uri = rdflib.URIRef(self.get_absolute_url())
        graph.add((page_uri, rdflib.RDF.type, self.rdf_type))
        # generate and add breadcrumbs, if any
        breadcrumbs = self.get_breadcrumbs()
        if breadcrumbs:
            breadcrumbs_node = rdflib.BNode()
            graph.set((page_uri, SCHEMA_ORG.breadcrumb, breadcrumbs_node))
            graph.set((breadcrumbs_node, rdflib.RDF.type, SCHEMA_ORG.BreadcrumbList))
            for pos, crumb in enumerate(breadcrumbs):
                crumb_node = rdflib.BNode()
                graph.add((breadcrumbs_node, SCHEMA_ORG.itemListElement, crumb_node))
                graph.set((crumb_node, rdflib.RDF.type, SCHEMA_ORG.ListItem))
                graph.set((crumb_node, SCHEMA_ORG.name, rdflib.Literal(crumb[0]))) # name/label
                graph.set((crumb_node, SCHEMA_ORG.item, rdflib.Literal(crumb[1]))) # url
                graph.set((crumb_node, SCHEMA_ORG.position, rdflib.Literal(pos + 1))) # position
        # output full graph
        return graph

    def get_breadcrumbs(self):
        '''Generate the breadcrumbs that lead to this page. Returns the value of
        `breadcrumbs` set on the View by default.'''
        return self.breadcrumbs


class VaryOnHeadersMixin(View):
    '''View mixin to set Vary header - class-based view equivalent to
    :meth:`django.views.decorators.vary.vary_on_headers`, adapted from
    winthrop-django.

    Define :attr:`vary_headers` with the list of headers.
    '''

    vary_headers = []

    def dispatch(self, request, *args, **kwargs):
        '''Wrap default dispatch method to patch haeders on the response.'''
        response = super(VaryOnHeadersMixin, self).dispatch(request, *args, **kwargs)
        patch_vary_headers(response, self.vary_headers)
        return response


class AjaxTemplateMixin(TemplateResponseMixin, VaryOnHeadersMixin):
    '''View mixin to use a different template when responding to an ajax
    request.'''

    #: name of the template to use for ajax request
    ajax_template_name = None
    #: vary on X-Request-With to avoid browsers caching and displaying
    #: ajax response for the non-ajax response
    vary_headers = ['X-Requested-With']

    def get_template_names(self):
        '''Return :attr:`ajax_template_name` if this is an ajax request;
        otherwise return default template name.'''
        if self.request.is_ajax():
            return self.ajax_template_name
        return super().get_template_names()

    def dispatch(self, request, *args, **kwargs):
        response = super(AjaxTemplateMixin, self).dispatch(request, *args, **kwargs)
        response['X-Total-Results'] = self.get_queryset().count()
        return response


class FacetJSONMixin(TemplateResponseMixin, VaryOnHeadersMixin):
    '''View mixin to respond with JSON representation of Solr facets when the
    HTTP Accept: header specifies application/json.'''

    #: vary on Accept: so that facets and results are cached separately
    vary_headers = ['Accept']

    def render_to_response(self, request, *args, **kwargs):
        '''Return a JsonResponse if the client asked for JSON, otherwise just
        call dispatch(). NOTE that this isn't currently smart enough to detect
        if the view's queryset is a SolrQuerySet; it will just break.'''
        if self.request.META.get('HTTP_ACCEPT') == 'application/json':
            return self.render_facets(request, *args, **kwargs)
        return super(FacetJSONMixin, self).render_to_response(request, *args, **kwargs)

    def render_facets(self, request, *args, **kwargs):
        '''Construct a JsonResponse based on the already-populated queryset
        data for the view.'''
        return JsonResponse(self.object_list.get_facets())


# last modified view mixin adapted from ppa


class SolrLastModifiedMixin(View):
    """View mixin to add last modified headers based on Solr"""

    # solr query filter for getting last modified date
    solr_lastmodified_filters = {}   # by default, find all
    #     filter_qs = ['item_type:work']

    def get_solr_lastmodified_filters(self):
        return self.solr_lastmodified_filters

    def last_modified(self):
        filter_qs = self.get_solr_lastmodified_filters()
        sqs = SolrQuerySet().filter(**filter_qs) \
            .order_by('-last_modified').only('last_modified')
        try:
            # Solr stores date in isoformat; convert to datetime
            return solr_timestamp_to_datetime(sqs[0]['last_modified'])
            # skip extra call to Solr to check count and just grab the first
            # item if it exists
        except (IndexError, KeyError):
            # if a syntax or other solr error happens, no date to return
            pass

    def dispatch(self, request, *args, **kwargs):
        # NOTE: this doesn't actually skip view processing,
        # but without it we could return a not modified for a non-200 response
        response = super(SolrLastModifiedMixin, self) \
            .dispatch(request, *args, **kwargs)

        last_modified = self.last_modified()
        if last_modified:
            # remove microseconds so that comparison will pass,
            # since microseconds are not included in the last-modified header
            last_modified = last_modified.replace(microsecond=0)
            response['Last-Modified'] = last_modified \
                .strftime('%a, %d %b %Y %H:%M:%S GMT')
            # convert the same way django does so that they will
            # compare correctly
            last_modified = calendar.timegm(last_modified.utctimetuple())

        return get_conditional_response(request, last_modified=last_modified,
                                        response=response)
