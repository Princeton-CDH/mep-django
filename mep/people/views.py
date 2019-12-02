from collections import OrderedDict, defaultdict

from dal import autocomplete
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.humanize.templatetags.humanize import ordinal
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin, FormView
from djiffy.models import Canvas

from mep.accounts.models import Address, Event
from mep.common import SCHEMA_ORG
from mep.common.utils import absolutize_url, alpha_pagelabels
from mep.common.views import (AjaxTemplateMixin, FacetJSONMixin,
                              LabeledPagesMixin, LoginRequiredOr404Mixin,
                              RdfViewMixin)
from mep.people.forms import MemberSearchForm, PersonMergeForm
from mep.people.geonames import GeoNamesAPI
from mep.people.models import Country, Location, Person
from mep.people.queryset import PersonSolrQuerySet


class MembersList(LoginRequiredOr404Mixin, LabeledPagesMixin, ListView,
                  FormMixin, AjaxTemplateMixin, FacetJSONMixin, RdfViewMixin):
    '''List page for searching and browsing library members.'''
    model = Person
    page_title = "Members"
    page_description = "Search and browse members by name and filter " + \
        "by date and demographics."
    template_name = 'people/member_list.html'
    ajax_template_name = 'people/snippets/member_results.html'
    paginate_by = 100
    context_object_name = 'members'
    rdf_type = SCHEMA_ORG.SearchResultsPage

    form_class = MemberSearchForm
    # cached form instance for current request
    _form = None
    #: initial form values
    initial = {
        'sort': 'name'
    }

    #: mappings for Solr field names to form aliases
    range_field_map = {
        'account_years': 'membership_dates',
    }
    #: fields to generate stats on in self.get_ranges
    stats_fields = ('account_years', 'birth_year')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # use GET instead of default POST/PUT for form data
        form_data = self.request.GET.copy()

        # always use relevance sort for keyword search;
        # otherwise use default (sort by name)
        if form_data.get('query', None):
            form_data['sort'] = 'relevance'
        else:
            form_data['sort'] = self.initial['sort']

        # use initial values as defaults
        for key, val in self.initial.items():
            form_data.setdefault(key, val)

        kwargs['data'] = form_data

        # get min/max configuration for range fields
        kwargs['range_minmax'] = self.get_range_stats()

        return kwargs

    def get_form(self, *args, **kwargs):
        # initialize the form, caching on current instance
        if not self._form:
            self._form = super().get_form(*args, **kwargs)
        return self._form

    def get_range_stats(self):
        """Return the min and max for fields specified in
        :class:`MembershipList`'s stats_fields

        :returns: Dictionary keyed on form field name with a tuple of
            (min, max) as integers. If stats are not returned from the field,
            the key is not added to a dictionary.
        :rtype: dict
        """

        stats = PersonSolrQuerySet().stats(*self.stats_fields).get_stats()
        min_max_ranges = {}
        if not stats:
            return min_max_ranges
        for name in self.stats_fields:
            try:
                min_year = int(stats['stats_fields'][name]['min'])
                max_year = int(stats['stats_fields'][name]['max'])
                # map to form field name if an alias is provided
                min_max_ranges[self.range_field_map.get(name, name)] \
                    = (min_year, max_year)
            # If the field stats are missing, min and max will be NULL,
            # rendered as None.
            # The TypeError will catch and pass returning an empty entry
            # for that field but allowing others to be passed on.
            except TypeError:
                pass
        return min_max_ranges

    #: name query alias field syntax (type defaults to edismax in solr config)
    search_name_query = '{!qf=$name_qf pf=$name_pf v=$name_query}'

    # map form sort to solr sort field
    solr_sort = {
        'relevance': '-score',
        'name': 'sort_name_sort_s'
    }

    def get_queryset(self):
        sqs = PersonSolrQuerySet() \
            .facet_field('has_card') \
            .facet_field('gender', missing=True, exclude='gender') \
            .facet_field('nationality', exclude='nationality', sort='value') \
            .facet_field('arrondissement', exclude='arrondissement',
                         sort='value')

        form = self.get_form()

        # empty queryset if not valid
        if not form.is_valid():
            sqs = sqs.none()

        # when form is valid, check for search term and filter queryset
        else:
            search_opts = form.cleaned_data

            if search_opts['query']:
                sqs = sqs.search(self.search_name_query) \
                         .raw_query_parameters(name_query=search_opts['query']) \
                         .also('score')  # include relevance score in results

            if search_opts['has_card']:
                sqs = sqs.filter(has_card=search_opts['has_card'])
            if search_opts['gender']:
                sqs = sqs.filter(gender__in=search_opts['gender'], tag='gender')
            if search_opts['nationality']:
                sqs = sqs.filter(nationality__in=[
                    '"%s"' % val for val in search_opts['nationality']
                ], tag='nationality')
            if search_opts['arrondissement']:
                # strip off ordinal letters and filter on numeric arrondissement
                sqs = sqs.filter(arrondissement__in=[
                    '%s' % val[:-2] for val in search_opts['arrondissement']
                ], tag='arrondissement')

            # range filter by membership dates, if set
            if search_opts['membership_dates']:
                sqs = sqs.filter(
                    account_years__range=search_opts['membership_dates'])
            # range filter by birth year, if set
            if search_opts['birth_year']:
                sqs = sqs.filter(birth_year__range=search_opts['birth_year'])

            # order based on solr name for search option
            sqs = sqs.order_by(self.solr_sort[search_opts['sort']])

        self.queryset = sqs
        return sqs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        facets = self.object_list.get_facets()['facet_fields']
        # convert arrondissement numbers into ordinals for display
        facets['arrondissement'] = OrderedDict([
            (ordinal(val), count)
            for val, count in facets['arrondissement'].items()
        ])
        self._form.set_choices_from_facets(facets)
        context.update({
            'page_title': self.page_title,
            'page_description': self.page_description
        })
        return context

    def get_page_labels(self, paginator):
        '''generate labels for pagination'''

        # if form is invalid, page labels should show 'N/A'
        form = self.get_form()
        if not form.is_valid():
            return [(1, 'N/A')]

        # when sorting by relevance, use default page label logic
        if form.cleaned_data['sort'] == 'relevance':
            return super().get_page_labels(paginator)

        # otherwise, when sorting by alpha, generate alpha page labels
        pagination_qs = self.queryset.only('sort_name')
        alpha_labels = alpha_pagelabels(paginator, pagination_qs,
                                        lambda x: x['sort_name'][0])

        # alpha labels is a dict; use items to return list of tuples
        return alpha_labels.items()

    def get_absolute_url(self):
        '''Get the full URI of this page.'''
        return absolutize_url(reverse('people:members-list'))

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        return [
            ('Home', absolutize_url('/')),
            (self.page_title, self.get_absolute_url()),
        ]


class MemberDetail(LoginRequiredOr404Mixin, DetailView, RdfViewMixin):
    '''Detail page for a single library member.'''
    model = Person
    template_name = 'people/member_detail.html'
    context_object_name = 'member'
    rdf_type = SCHEMA_ORG.ProfilePage

    def get_queryset(self):
        # throw a 404 if a non-member is accessed via this route
        return super().get_queryset().exclude(account=None)

    def get_absolute_url(self):
        '''Get the full URI of this page.'''
        return absolutize_url(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # add account to context for convenience
        account = self.object.account_set.first()
        context['account'] = account

        month_counts = defaultdict(int)
        # count book events by month; known years only
        for event in account.event_set.known_years().book_activities():
            if event.start_date:
                month_counts[event.start_date.strftime('%Y-%m-01')] += 1
            # if end date is different from start date, count that also
            if event.end_date and event.start_date != event.end_date:
                month_counts[event.end_date.strftime('%Y-%m-01')] += 1

        # data for member timeline visualization
        context['timeline'] = {
            'membership_activities': [{
                'startDate': event.start_date.isoformat()
                if event.start_date else '',
                'endDate': event.end_date.isoformat()
                if event.end_date else '',
                'type': event.event_type
            } for event in account.event_set.membership_activities()
                                  .known_years()],
            'book_activities': [{
                'startDate': start_date,
                'count': count
            } for start_date, count in month_counts.items()],
            'activity_ranges': [{
                'startDate': start.isoformat(),
                'endDate': end.isoformat()
            } for start, end in account.event_date_ranges()]
        }

        # plottable locations for member address map visualization, which
        # is a leaflet map that will consume JSON address data
        # NOTE probably refactor this into a queryset method for use on
        # members search map
        addresses = Address.objects.filter(account=account) \
            .filter(location__latitude__isnull=False) \
            .filter(location__longitude__isnull=False)

        context['addresses'] = [
            {
                # these fields are taken from Location unchanged
                'name': address.location.name,
                'street_address': address.location.street_address,
                'city': address.location.city,
                'postal_code': address.location.postal_code,
                # lat/long aren't JSON serializable so we need to do this
                'latitude': str(address.location.latitude),
                'longitude': str(address.location.longitude),
                # NOTE not currently using dates as they're not entered yet
            }
            for address in addresses]

        # address of the lending library itself; automatically available from
        # migration mep/people/migrations/0014_library_location.py
        library = Location.objects.get(name='Shakespeare & Company')
        context['library_address'] = {
            'name': library.name,
            'street_address': library.street_address,
            'city': library.city,
            'latitude': str(library.latitude),
            'longitude': str(library.longitude),
        }

        # config settings used to render the map; set in local_settings.py
        context.update({
            'mapbox_token': getattr(settings, 'MAPBOX_ACCESS_TOKEN', ''),
            'mapbox_basemap': getattr(settings, 'MAPBOX_BASEMAP', ''),
            'paris_overlay': getattr(settings, 'PARIS_OVERLAY', ''),
            # metadata for social preview
            'page_title': self.object.firstname_last
        })

        return context

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        return [
            ('Home', absolutize_url('/')),
            (MembersList.page_title, MembersList().get_absolute_url()),
            (self.object.short_name, self.get_absolute_url())
        ]


class MembershipActivities(LoginRequiredOr404Mixin, ListView, RdfViewMixin):
    '''Display a list of membership activities (subscriptions, renewals,
    and reimbursements) for an individual member.'''
    model = Event
    template_name = 'people/membership_activities.html'
    # tooltip text shown to explain the 'category' column in the table
    CATEGORY_TOOLTIP = 'More information coming soon.'

    def get_queryset(self):
        # filter to requested person, then get membership activities
        return super().get_queryset() \
                      .filter(account__persons__slug=self.kwargs['slug']) \
                      .membership_activities()

    def get_context_data(self, **kwargs):
        # should 404 if not a person or valid person but not a library member
        # store member before calling super so available for breadcrumbs
        self.member = get_object_or_404(Person.objects.library_members(),
                                        slug=self.kwargs['slug'])
        context = super().get_context_data(**kwargs)
        context.update({
            'member': self.member,
            'category_tooltip': self.CATEGORY_TOOLTIP,
            'page_title': '%s Membership Activity' % self.member.firstname_last
        })
        return context

    def get_absolute_url(self):
        '''Get the full URI of this page.'''
        return absolutize_url(reverse('people:membership-activities',
                                      kwargs=self.kwargs))

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        return [
            ('Home', absolutize_url('/')),
            (MembersList.page_title, MembersList().get_absolute_url()),
            (self.member.short_name,
             absolutize_url(self.member.get_absolute_url())),
            ('Membership', self.get_absolute_url())
        ]


class BorrowingActivities(LoginRequiredOr404Mixin, ListView, RdfViewMixin):
    '''Display a list of book-related activities (borrows, purchases, gifts)
    for an individual member.'''
    model = Event
    template_name = 'people/borrowing_activities.html'

    def get_queryset(self):
        # filter to requested person, then get book activities
        return super().get_queryset() \
                      .filter(account__persons__slug=self.kwargs['slug']) \
                      .book_activities() \
                      .select_related('borrow', 'purchase', 'work') \
                      .prefetch_related('work__creators', 'work__creator_set',
                                        'work__creator_set__creator_type')

    def get_context_data(self, **kwargs):
        # should 404 if not a person or valid person but not a library member
        # store member before calling super so available for breadcrumbs
        self.member = get_object_or_404(Person.objects.library_members(),
                                        slug=self.kwargs['slug'])
        context = super().get_context_data(**kwargs)
        context.update({
            'member': self.member,
            'page_title': '%s Borrowing Activity' % self.member.firstname_last
        })
        return context

    def get_absolute_url(self):
        '''Get the full URI of this page.'''
        return absolutize_url(reverse('people:borrowing-activities',
                                      kwargs=self.kwargs))

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        return [
            ('Home', absolutize_url('/')),
            (MembersList.page_title, MembersList().get_absolute_url()),
            (self.member.short_name,
                absolutize_url(self.member.get_absolute_url())),
            ('Borrowing', self.get_absolute_url())
        ]


class MemberCardList(LoginRequiredOr404Mixin, ListView, RdfViewMixin):
    '''Card thumbnails for lending card associated with a single library
    member.'''
    model = Canvas
    template_name = 'people/member_cardlist.html'
    context_object_name = 'cards'

    def get_queryset(self):
        # find the associated member; 404 if not found or not a library member
        self.member = get_object_or_404(Person.objects.library_members(),
                                        slug=self.kwargs['slug'])
        # find all canvas objects for this person, via manifest
        # associated with lending card bibliography
        return super().get_queryset() \
                      .filter(manifest__bibliography__account__persons__slug=self.kwargs['slug']) \
                      .order_by('order')

    def get_absolute_url(self):
        '''Full URI for member card list page.'''
        return absolutize_url(reverse('people:member-card-list',
                                      kwargs=self.kwargs))

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        return [
            ('Home', absolutize_url('/')),
            (MembersList.page_title, MembersList().get_absolute_url()),
            (self.member.short_name,
             absolutize_url(self.member.get_absolute_url())),
            ('Cards', self.get_absolute_url())
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.member
        return context


class MemberCardDetail(LoginRequiredOr404Mixin, DetailView, RdfViewMixin):
    '''Card image viewer for image of a single lending card page
    associated with a single library member.'''
    model = Canvas
    template_name = 'people/member_card_detail.html'
    context_object_name = 'card'

    def get_object(self):
        # find the associated member; 404 if not found or not a library member
        self.member = get_object_or_404(Person.objects.library_members(),
                                        slug=self.kwargs['slug'])
        # find requested canvas objects for this person, via manifest
        # associated with lending card bibliography
        filters = {
            'short_id': self.kwargs['short_id'],
            'manifest__bibliography__account__persons__slug':
            self.kwargs['slug']
        }
        # return super().get_queryset().filter(**filters)
        card = get_object_or_404(Canvas.objects.all(), **filters)
        # use card dates for label
        card_dates = card.footnote_set.event_date_range()
        label = 'Unknown'
        if card_dates:
            label = card_dates[0].year
            if card_dates[1].year != card_dates[0].year:
                label = '%s – %s' % (label, card_dates[1].year)

        self.label = label
        return card

    def get_absolute_url(self):
        '''Full URI for member card list page.'''
        return absolutize_url(reverse('people:member-card-detail',
                                      kwargs=self.kwargs))

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        return [
            ('Home', absolutize_url('/')),
            (MembersList.page_title, MembersList().get_absolute_url()),
            (self.member.short_name,
             absolutize_url(self.member.get_absolute_url())),
            ('Cards', absolutize_url(reverse('people:member-card-list',
                                     kwargs={'slug': self.member.slug}))),
            (self.label, self.get_absolute_url())
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # use order within manifest to get next/prev links
        sibling_cards = self.object.manifest.canvases
        next_card = sibling_cards.filter(order=self.object.order + 1).first()
        prev_card = sibling_cards.filter(order=self.object.order - 1).first()
        context.update({
            'member': self.member,
            'label': self.label,
            'events': self.object.footnote_set.events(),
            'next_card': next_card,
            'prev_card': prev_card
        })
        return context


class MembershipGraphs(LoginRequiredOr404Mixin, TemplateView):
    model = Person
    template_name = 'people/member_graphs.html'

    def get_context_data(self):
        context = super().get_context_data()

        # use facets to get member totals by month and year
        sqs = PersonSolrQuerySet() \
            .facet_field('account_yearmonths', sort='index', limit=1000) \
            .facet_field('logbook_yearmonths', sort='index', limit=1000) \
            .facet_field('card_yearmonths', sort='index', limit=1000)

        facets = sqs.get_facets()['facet_fields']

        context['data'] = {
            # convert into a format that's easier to use with javascript/d3
            'members': [{
                'startDate': '%s-%s-01' % (yearmonth[:4], yearmonth[-2:]),
                'count': count
            } for yearmonth, count in facets['account_yearmonths'].items()
            ],
            'logbooks': [{
                'startDate': '%s-%s-01' % (yearmonth[:4], yearmonth[-2:]),
                'count': count
            } for yearmonth, count in facets['logbook_yearmonths'].items()
            ],
            'cards': [{
                'startDate': '%s-%s-01' % (yearmonth[:4], yearmonth[-2:]),
                'count': count
            } for yearmonth, count in facets['card_yearmonths'].items()
            ]

        }
        return context


class GeoNamesLookup(autocomplete.Select2ListView):
    '''GeoNames ajax lookup for use as autocomplete.
    Optional mode parameter to restrict to countries only.
    '''

    mode = None

    def get(self, request, mode=None, *args, **kwargs):
        """"Return option list json response."""
        geo_api = GeoNamesAPI()
        extra_args = {}
        self.mode = mode

        # restrict to countries when requested
        if self.mode == 'country':
            extra_args.update({
                'feature_class': 'A',
                'feature_code': 'PCLI',
            })

        results = geo_api.search(self.q, max_rows=50, name_start=True,
                                 **extra_args)
        return JsonResponse({
            'results': [dict(
                id=geo_api.uri_from_id(item['geonameId']),
                text=self.get_label(item),
                name=item['name'],
                country_code=item['countryCode'],
                # lat & long included in data to make them available for
                # javascript to populateform fields
                lat=item['lat'],
                lng=item['lng']
            ) for item in results],
        })

    def get_label(self, item):
        '''display country for context, if available'''
        if self.mode != 'country' and 'countryName' in item:
            # FIXME: shouldn't ever display countryname if item is a country
            return '''%(name)s, %(countryName)s''' % item
        return item['name']


class PersonAutocomplete(autocomplete.Select2QuerySetView):
    '''
    Basic person autocomplete lookup, for use with django-autocomplete-light.
    Use Q objects to help distinguish people using mepid.
    '''

    def get_result_label(self, person):
        '''
        Provide a more detailed result label for the people autocomplete that
        can help disambiguate people.

        '''
        # Fields that will be formatted before interpolation
        labels = {
            'main_string': '',
            'bio_dates': '',
            'note_string': '',
        }
        # title and name, stripped in case title is absent so no stray space
        labels['main_string'] = \
            ('%s %s' % (person.title, person.name)).strip()
        # format birth-death in a familiar pattern ( - )
        if person.birth_year or person.death_year:
            labels['bio_dates'] = \
                ' (%s–%s)' % (person.birth_year, person.death_year)
        # get the first few words of any notes
        if person.notes:
            list_notes = person.notes.split()
            labels['note_string'] = ' '.join(list_notes[:5])
        # padding id with a space so that it looks nice in the formatted
        # html and we don't have to worry about stripping it in the
        # interpolated text.
        labels['mep_id'] = (' %s' % person.mep_id) if person.mep_id else ''
        if not labels['bio_dates'] and not labels['note_string']:
            # in situations where there are none of the above,
            # pull the first event
            if person.account_set.first():
                event = Event.objects.filter(
                    account=person.account_set.first()
                ).order_by('start_date').first()
                # if it has a first event (not all do), return that event
                if event:
                    labels['start_date'] = event.start_date
                    labels['end_date'] = (event.end_date
                                          if event.end_date else '')
                    labels['type'] = event.event_type
                    return format_html(
                        '<strong>{main_string}</strong>'
                        '{mep_id} <br />{type} '
                        '({start_date}–{end_date})'.strip(),
                        **labels
                    )
            return format_html('<strong>{main_string}</strong>{mep_id}',
                               **labels)
        # we have some of the information, return it in an interpolated string
        return format_html(
            '<strong>{main_string}{bio_dates}'
            '</strong>{mep_id}<br /> {note_string}'.strip(),
            **labels
        )

    def get_queryset(self):
        ''':class:`~mep.people.models.Person` queryset, filtered on
        text in name or MEP id (case-insensitive, partial match)'''
        return Person.objects.filter(
            Q(name__icontains=self.q) |
            Q(mep_id__icontains=self.q)
        )


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.people.models.Person` in nationalities many-to-many.
    '''

    def get_queryset(self):
        ''':class:`~mep.people.models.Country` queryset, filtered on
        text in name (case-insensitive, partial match)'''
        return Country.objects.filter(name__icontains=self.q)


class LocationAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.people.models.Person` in address many-to-many'''

    def get_queryset(self):
        '''
        Get queryset of :class:`mep.people.models.Location` objects.
        Use Q objects to search all relevant fields in autocomplete.
        '''
        # not searching lat or lon for now
        return Location.objects.filter(
            Q(name__icontains=self.q) |
            Q(street_address__icontains=self.q) |
            Q(city__icontains=self.q) |
            Q(postal_code__icontains=self.q) |
            Q(country__name__icontains=self.q) |
            Q(address__person__name__icontains=self.q)
        ).order_by('name', 'city', 'street_address')


class PersonMerge(PermissionRequiredMixin, FormView):
    '''View method to merge one or more :class:`~mep.people.models.Person`
    records.  Displays :class:`~mep.people.models.PersonMergeForm` on
    GET, processes merge with :meth:`mep.people.models.PersonQuerySet.merge_with`
    on successful POST.  Should be called with a list of person ids
    in the querystring as a comma-separated list. Created for use
    with custom admin action
    :meth:`mep.people.admin.PersonAdmin.merge_people`.
    '''

    permission_required = ('people.change_person', 'people.delete_person')
    form_class = PersonMergeForm
    template_name = 'people/merge_person.html'

    def get_success_url(self):
        '''
        Redirect to the :class:`mep.people.models.Person` change_list in the
        Django admin with pagination and filters preserved.
        Expects :meth:`mep.people.admin.PersonAdmin.merge_people`
        to have set 'people_merge_filter' in the request's session.
        '''
        change_list = reverse('admin:people_person_changelist')
        # get request.session's querystring filter, if it exists,
        # use rstrip to remove the ? so that we're left with an empty string
        # otherwise
        querystring = ('?%s' %
                       self.request.session.
                       get('people_merge_filter', '')).rstrip('?')
        return '%s%s' % (change_list, querystring)

    def get_form_kwargs(self):
        form_kwargs = super(PersonMerge, self).get_form_kwargs()
        form_kwargs['person_ids'] = self.person_ids
        return form_kwargs

    def get_initial(self):
        # default to first person selected (?)
        # _could_ add logic to select most complete record,
        # but probably better for team members to choose
        person_ids = self.request.GET.get('ids', None)
        if person_ids:
            self.person_ids = [int(pid) for pid in person_ids.split(',')]
            # by default, prefer the first record created
            return {'primary_person': sorted(self.person_ids)[0]}

        self.person_ids = []

    def form_valid(self, form):
        # process the valid POSTed form

        # user-selected person record to keep
        primary_person = form.cleaned_data['primary_person']
        existing_events = 0
        existing_creators = 0

        if primary_person.has_account():  # get existing events, if any
            primary_account = primary_person.account_set.first()
            existing_events = primary_account.event_set.count()

        if primary_person.is_creator():
            existing_creators = primary_person.creator_set.count()

        try:
            # find duplicate person records to be consolidated and merge
            Person.objects.filter(id__in=self.person_ids) \
                          .merge_with(primary_person)

            message = 'Merge for <a href="%s">%s</a> complete.' % (
                reverse('admin:people_person_change',
                        args=[primary_person.id]),
                primary_person
            )

            if primary_person.has_account():  # calculate events reassociated
                primary_account = primary_person.account_set.first()  # if there wasn't one before
                added_events = primary_account.event_set.count() - existing_events
                message += ' Reassociated %d event%s with <a href="%s">%s</a>.' % (
                    added_events,
                    's' if added_events != 1 else '',
                    reverse('admin:accounts_account_change',
                            args=[primary_account.id]),
                    primary_account
                )
            else:  # no accounts merged
                message += ' No accounts to reassociate.'

            if primary_person.is_creator():  # calculate creator roles reassociated
                added_creators = primary_person.creator_set.count() - existing_creators
                message += ' Reassociated %d creator role%s on items.' % (
                    added_creators,
                    's' if added_creators != 1 else ''
                )
            else:  # no creators reassociated
                message += ' No creator relationships to reassociate.'

            messages.success(self.request, mark_safe(message))

        # error if person has more than one account
        except MultipleObjectsReturned as err:
            messages.error(self.request, str(err))

        return super(PersonMerge, self).form_valid(form)
