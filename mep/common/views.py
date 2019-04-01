from django.views.generic.base import View, ContextMixin
from django.core.paginator import Paginator

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
            page_start = (page - 1) * paginator.per_page
            page_end = page_start + paginator.per_page
            # final page should end at number of the final item
            if page_end > paginator.count:
                page_end = paginator.count
            page_labels.append((page, '%d - %d' % (page_start + 1, page_end)))
        return page_labels

    def get_context_data(self: View, **kwargs):
        '''Add generated page labels to the view context.'''
        context = super().get_context_data(**kwargs)
        paginator = context['page_obj'].paginator
        context['page_labels'] = self.get_page_labels(paginator)
        return context
