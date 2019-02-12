import csv

from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q
from django.http import JsonResponse, StreamingHttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from parasol.solr.django import SolrClient
from parasol.query import SolrQuerySet

from mep.accounts.models import Event
from mep.people.forms import PersonMergeForm
from mep.people.geonames import GeoNamesAPI
from mep.people.models import Country, Location, Person


class MembersList(ListView):
    '''List page for searching and browsing library members.'''
    model = Person
    template_name = 'people/member_list.html'
    # pagination not yet designed
    # paginate_by = 100
    context_object_name = 'members'

    def get_queryset(self):
        sqs = SolrQuerySet().filter(item_type='person') \
                            .order_by('sort_name_sort_s') \

        # NOTE: using [:100000] to make sure we retrieve everything
        # (remove when we turn on pagination)
        sqs = sqs[:10000]

        # TODO: add field limit and alias like this with
        # fl='name:name_t,sort_name:sort_name_t',

        return sqs




class MemberDetail(DetailView):
    '''Detail page for a single library member.'''
    model = Person
    template_name = 'people/member_detail.html'
    context_object_name = 'member'

    def get_queryset(self):
        # throw a 404 if a non-member is accessed via this route
        return super().get_queryset().exclude(account=None)


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
                ' (%s - %s)' % (person.birth_year, person.death_year)
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
                        '({start_date} - {end_date})'.strip(),
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

        else:
            self.person_ids = []

    def form_valid(self, form):
        # process the valid POSTed form

        # user-selected person record to keep
        primary_person = form.cleaned_data['primary_person']
        existing_events = 0
        existing_creators = 0

        if primary_person.has_account(): # get existing events, if any
            primary_account = primary_person.account_set.first()
            existing_events = primary_account.event_set.count()

        if primary_person.is_creator():
            existing_creators = primary_person.creator_set.count()

        try:
            # find duplicate person records to be consolidated and merge
            Person.objects.filter(id__in=self.person_ids) \
                          .merge_with(primary_person)

            message = 'Merge for <a href="%s">%s</a> complete.' % (
                reverse('admin:people_person_change', args=[primary_person.id]),
                primary_person
            )

            if primary_person.has_account(): # calculate events reassociated
                primary_account = primary_person.account_set.first() # if there wasn't one before
                added_events = primary_account.event_set.count() - existing_events
                message += ' Reassociated %d event%s with <a href="%s">%s</a>.' % (
                    added_events,
                    's' if added_events != 1 else '',
                    reverse('admin:accounts_account_change', args=[primary_account.id]),
                    primary_account
                )
            else: # no accounts merged
                message += ' No accounts to reassociate.'

            if primary_person.is_creator(): # calculate creator roles reassociated
                added_creators = primary_person.creator_set.count() - existing_creators
                message += ' Reassociated %d creator role%s on items.' % (
                    added_creators,
                    's' if added_creators != 1 else ''
                )
            else: # no creators reassociated
                message += ' No creator relationships to reassociate.'

            messages.success(self.request, mark_safe(message))

        # error if person has more than one account
        except MultipleObjectsReturned as err:
            messages.error(self.request, str(err))

        return super(PersonMerge, self).form_valid(form)
