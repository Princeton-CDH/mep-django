from django.core.paginator import Paginator
from django.utils.cache import patch_vary_headers
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View


class LabeledPagesMixin(ContextMixin):
    '''View mixin to add labels for pages to a paginated view's context,
    for use in rendering pagination controls.'''

    def get_page_labels(self: View, paginator: Paginator):
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
            page_labels.append((page, '%d - %d' % (page_start + 1, page_end)))
        return page_labels

    def get_context_data(self: View, **kwargs):
        '''Add generated page labels to the view context.'''
        context = super().get_context_data(**kwargs)
        paginator = context['page_obj'].paginator
        context['page_labels'] = self.get_page_labels(paginator)
        return context


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
