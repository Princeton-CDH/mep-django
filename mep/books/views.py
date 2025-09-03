from dal import autocomplete
from django.db.models import F, Q
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin


from mep.accounts.models import Event
from mep.accounts.templatetags.account_tags import as_ranges
from mep.books.forms import WorkSearchForm
from mep.books.models import Work
from mep.books.queryset import WorkSolrQuerySet
from mep.common import SCHEMA_ORG
from mep.common.utils import absolutize_url, alpha_pagelabels
from mep.common.views import (
    AjaxTemplateMixin,
    FacetJSONMixin,
    LabeledPagesMixin,
    RdfViewMixin,
    SolrLastModifiedMixin,
)
from mep.footnotes.models import Footnote
from mep.pages.models import LinkPage


class WorkList(
    LabeledPagesMixin,
    SolrLastModifiedMixin,
    ListView,
    FormMixin,
    AjaxTemplateMixin,
    FacetJSONMixin,
    RdfViewMixin,
):
    """List page for searching and browsing library items."""

    model = Work
    page_title = "Books"
    page_description = (
        "Search and lending library books by title, author,"
        + " or keyword and filter by circulation date."
    )
    template_name = "books/work_list.html"
    ajax_template_name = "books/snippets/work_results.html"
    paginate_by = 100
    context_object_name = "works"
    rdf_type = SCHEMA_ORG.SearchResultPage
    solr_lastmodified_filters = {"item_type": "work"}

    form_class = WorkSearchForm
    _form = None
    initial = {"sort": "title"}

    #: mappings for Solr field names to form aliases
    range_field_map = {
        "event_years": "circulation_dates",
    }

    #: fields to generate stats on in self.get_ranges
    stats_fields = ("event_years",)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        form_data = self.request.GET.copy()

        # set defaults
        for key, val in self.initial.items():
            form_data.setdefault(key, val)

        # set relevance sort as default when there is a search term
        if form_data.get("query", None):
            form_data.setdefault("sort", "relevance")

        kwargs["data"] = form_data
        # get min/max configuration for range fields
        kwargs["range_minmax"] = self.get_range_stats()

        return kwargs

    # adapted from member list view
    def get_range_stats(self):
        """Return the min and max for fields specified in
        :class:`WorkList`'s stats_fields

        :returns: Dictionary keyed on form field name with a tuple of
            (min, max) as integers. If stats are not returned from the field,
            the key is not added to a dictionary.
        :rtype: dict
        """
        stats = WorkSolrQuerySet().stats(*self.stats_fields).get_stats()
        min_max_ranges = {}
        if not stats:
            return min_max_ranges
        for name in self.stats_fields:
            try:
                min_year = int(stats["stats_fields"][name]["min"])
                max_year = int(stats["stats_fields"][name]["max"])
                # map to form field name if an alias is provided
                min_max_ranges[self.range_field_map.get(name, name)] = (
                    min_year,
                    max_year,
                )
            # If the field stats are missing, min and max will be NULL,
            # rendered as None.
            # The TypeError will catch and pass returning an empty entry
            # for that field but allowing others to be passed on.
            except TypeError:
                pass
        return min_max_ranges

    def get_form(self, *args, **kwargs):
        if not self._form:
            self._form = super().get_form(*args, **kwargs)
        return self._form

    # map form sort to solr sort
    solr_sort = {
        "relevance": "-score",
        "title": "sort_title_isort",
        "author": "sort_authors_isort",
        "pubdate": "-pub_date_i",
        "circulation": "-event_count_i",
        "circulation_date": "first_event_date_i",
    }
    # NOTE: might be able to infer reverse sort from _desc/_za
    # instead of hard-coding here

    #: bib data query alias field syntax (configured defaults is edismax)
    search_bib_query = "{!type=edismax qf=$bib_qf pf=$bib_pf v=$bib_query}"

    def get_queryset(self):
        # NOTE faceting so that response doesn't register as an error;
        # data is currently unused
        sqs = WorkSolrQuerySet().facet_field("format", exclude="format")

        form = self.get_form()

        # empty qs if not valid
        if not form.is_valid():
            sqs = sqs.none()

        # otherwise apply filters, query, sort, etc.
        else:
            search_opts = form.cleaned_data

            if search_opts.get("query", None):
                sqs = (
                    sqs.search(self.search_bib_query)
                    .raw_query_parameters(bib_query=search_opts["query"])
                    .also("score")
                )  # include relevance score in results

            sort_opt = self.solr_sort[search_opts["sort"]]
            sqs = sqs.order_by(sort_opt)
            # when not sorting by title, use title as secondary sort
            if self.solr_sort["title"] not in sort_opt:
                sqs = sqs.order_by(self.solr_sort["title"])

            # range filter by circulation dates, if set
            if search_opts["circulation_dates"]:
                sqs = sqs.filter(event_years__range=search_opts["circulation_dates"])

        self.queryset = sqs
        return sqs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        facets = self.object_list.get_facets().get("facet_fields", None)
        error_message = ""
        # facets are not set if there is an error on the query
        if facets:
            self._form.set_choices_from_facets(facets)
        else:
            # if facets are not set, the query errored
            error_message = "Something went wrong."

        # allow page_title override via wagtail
        try:
            link_page = LinkPage.objects.get(link_url="/books")
            page_title = link_page.title
        except LinkPage.DoesNotExist:
            page_title = self.page_title

        context.update(
            {
                "page_title": page_title,
                "page_description": self.page_description,
                "error_message": error_message,
                "uncertainty_message": Work.UNCERTAINTY_MESSAGE,
            }
        )
        return context

    def get_page_labels(self, paginator):
        """generate labels for pagination"""

        # if form is invalid, page labels should show 'N/A'
        form = self.get_form()
        if not form.is_valid():
            return [(1, "N/A")]
        sort = form.cleaned_data["sort"]

        if sort in ["title", "author", "pubdate", "circulation_date"]:
            sort_field = self.solr_sort[sort].lstrip("-")
            # otherwise, when sorting by alpha, generate alpha page labels
            # Only return sort name; get everything at once to avoid
            # hitting Solr for each page / item.
            pagination_qs = self.queryset.only(sort_field).get_results(rows=100000)
            # cast to string so integers (year) can be treated the same
            alpha_labels = alpha_pagelabels(
                paginator,
                pagination_qs,
                lambda x: str(x.get(sort_field, "")),
                max_chars=4,
            )
            # alpha labels is a dict; use items to return list of tuples
            return alpha_labels.items()

        # otherwise use default page label logic
        return super().get_page_labels(paginator)

    def get_absolute_url(self):
        """Get the full URI of this page."""
        return absolutize_url(reverse("books:books-list"))

    def get_breadcrumbs(self):
        """Get the list of breadcrumbs and links to display for this page."""
        # NOTE we can't set this as an attribute on the view because it calls
        # reverse() via get_absolute_url(), which needs the urlconf to be loaded
        return [
            ("Home", absolutize_url("/")),
            (self.page_title, self.get_absolute_url()),
        ]


class WorkLastModifiedListMixin(SolrLastModifiedMixin):
    """last modified mixin with common logic for all work detail views"""

    def get_solr_lastmodified_filters(self):
        """filter solr query by item type and slug"""
        # NOTE: slug_s because not using aliased queryset
        return {"item_type": "work", "slug_s": self.kwargs["slug"]}


class WorkPastSlugMixin:
    """View mixin to handle redirects for previously used slugs.
    If the main view logic raises a 404, looks for a work
    by past slug; if one is found, redirects to the corresponding
    work detail page with the new slug.
    """

    def get(self, request, *args, **kwargs):
        """Handle a 404 on the default GET logic — if the slug matches
        a past slug, redirect to the equivalent url for that work; otherwise
        raise the 404."""
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            # if not found, check for a match on a past slug
            work = Work.objects.filter(past_slugs__slug=self.kwargs["slug"]).first()
            # if found, redirect to the correct url for this view
            if work:
                # patch in the correct slug for use with get absolute url
                self.kwargs["slug"] = work.slug
                self.object = work  # used by member detail absolute url
                return HttpResponsePermanentRedirect(self.get_absolute_url())

            # otherwise, raise the 404
            raise


class WorkDetail(
    WorkPastSlugMixin, WorkLastModifiedListMixin, DetailView, RdfViewMixin
):
    """Detail page for a single library book."""

    model = Work
    template_name = "books/work_detail.html"
    context_object_name = "work"
    rdf_type = SCHEMA_ORG.ItemPage

    def get_absolute_url(self):
        """Get the full URI of this page."""
        return absolutize_url(self.object.get_absolute_url())

    def get_breadcrumbs(self):
        """Get the list of breadcrumbs and links to display for this page."""
        return [
            ("Home", absolutize_url("/")),
            (WorkList.page_title, WorkList().get_absolute_url()),
            (self.object.title, self.get_absolute_url()),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        description = ""
        if self.object.authors:
            description = "By %s" % ",".join([a.name for a in self.object.authors])
        if self.object.year:
            description += ", %s" % self.object.year
        description += ". "

        # text-only readable version of membership years for meta description
        circ_years = strip_tags(
            as_ranges(self.object.event_years).replace("</span>", ",")
        ).rstrip(",")

        description += "%d event%s in %s. " % (
            self.object.event_count,
            "" if self.object.event_count == 1 else "s",
            circ_years,
        )
        if self.object.public_notes:
            description += self.object.public_notes

        context.update(
            {
                "page_title": self.object.title,
                "page_description": description,
            }
        )
        return context


class WorkCirculation(
    WorkPastSlugMixin, WorkLastModifiedListMixin, ListView, RdfViewMixin
):
    """Display a list of circulation events (borrows, purchases, etc)
    for an individual work."""

    model = Event
    template_name = "books/circulation.html"

    def get_queryset(self):
        """Fetch all events associated with this work."""
        return (
            super()
            .get_queryset()
            .filter(work__slug=self.kwargs["slug"])
            .select_related("borrow", "purchase", "account", "edition")
            .prefetch_related("account__persons")
        )

    def get_context_data(self, **kwargs):
        # should 404 if invalid work slug
        # store work before calling super() so available for breadcrumbs
        self.work = get_object_or_404(Work, slug=self.kwargs["slug"])
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "work": self.work,
                "page_title": "%s Circulation Activity" % self.work.title,
            }
        )
        return context

    def get_absolute_url(self):
        """Get the full URI of this page."""
        return absolutize_url(reverse("books:book-circ", kwargs=self.kwargs))

    def get_breadcrumbs(self):
        """Get the list of breadcrumbs and links to display for this page."""
        return [
            ("Home", absolutize_url("/")),
            (WorkList.page_title, WorkList().get_absolute_url()),
            (self.work.title, absolutize_url(self.work.get_absolute_url())),
            ("Circulation", self.get_absolute_url()),
        ]


class WorkCardList(
    WorkPastSlugMixin, WorkLastModifiedListMixin, ListView, RdfViewMixin
):
    """Card thumbnails for lending card associated with a single library
    member."""

    model = Footnote
    template_name = "books/work_cardlist.html"
    context_object_name = "footnotes"

    def get_queryset(self):
        # find the associated book; 404 if not found
        self.work = get_object_or_404(Work, slug=self.kwargs["slug"])

        # find footnotes for events associated with this work
        # that have images
        return (
            super()
            .get_queryset()
            .on_events()
            .filter(events__work__pk=self.work.pk)
            .filter(image__isnull=False)
            .prefetch_related("content_object", "image")
            .order_by(
                F("events__start_date_precision").desc(),
                F("events__start_date").asc(nulls_last=True),
            )
        )

        # NOTE: sorting by date precision decending (with default nulls first)
        # so that full precision dates (null or 7) come before partial dates

    def get_absolute_url(self):
        """Full URI for work card list page."""
        return absolutize_url(reverse("books:book-card-list", kwargs=self.kwargs))

    def get_breadcrumbs(self):
        """Get the list of breadcrumbs and links to display for this page."""
        return [
            ("Home", absolutize_url("/")),
            (WorkList.page_title, WorkList().get_absolute_url()),
            (self.work.title, absolutize_url(self.work.get_absolute_url())),
            ("Cards", self.get_absolute_url()),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_title = "Lending library cards that reference %s" % self.work.title
        # there should always be at least one card, but handle in
        # case of data errors
        page_image = None
        if self.object_list.count():
            page_image = self.object_list.first().image.image
        card_count = self.object_list.count()
        page_description = "%d card%s" % (card_count, "s" if card_count != 1 else "")

        context.update(
            {
                "work": self.work,
                "page_title": page_title,
                "page_description": page_description,
                "page_iiif_image": page_image,
            }
        )
        return context


class WorkAutocomplete(autocomplete.Select2QuerySetView):
    """Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.books.models.Work` for borrowing and purchasing events"""

    def get_queryset(self):
        """Get a queryset filtered by query string. Only
        searches on title, mep id and notes for now, since that is all
        our stub records include.
        """
        return Work.objects.filter(
            Q(title__icontains=self.q)
            | Q(mep_id__icontains=self.q)
            | Q(notes__icontains=self.q)
        ).order_by(
            "title"
        )  # meaningful default sort?
