from django.db.models import Q
from django.http import JsonResponse
from django.utils.html import format_html
from dal import autocomplete

from mep.accounts.models import Event
from mep.people.geonames import GeoNamesAPI
from mep.people.models import Address, Country, Person


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
        # display country for context, if available
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
        '''Provide a more result label for the people autocomplete that can
        help disambiguate people'''
        # Fields that will be formatted before interpolation
        bio_dates = ''
        note_string = ''
        mep_id = ''
        # title and name, stripped in case title is absent so no stray space
        main_string = ('%s %s' % (person.title, person.name)).strip()
        # format birth-death in a familiar pattern
        if person.birth_year or person.death_year:
            bio_dates = ' (%s - %s)' % (person.birth_year, person.death_year)
        # get the first few words of any notes
        if person.notes:
            list_notes = person.notes.split()
            note_string = ' '.join(list_notes[:5])
        if person.mep_id:
            # padding id with a space so that it looks nice in the formatted
            # html
            mep_id = ' %s' % mep_id

        # in situations where there are none of these, pull their first event
        if not bio_dates or note_string or mep_id:
            # if the person has an account get its first event
            if person.account_set.first():
                event = Event.objects.filter(
                        account=person.account_set.first()
                    ).first()
                # if it has a first event (not all do), return that event
                if event:
                    return format_html(
                            '<strong>{}</strong><br />{} {}', main_string,
                            event.start_date, event.event_type
                        )
            return format_html('<strong>{}</strong>', main_string)
        return format_html(
                    '<strong>{}{}</strong><br>{}{}'.strip(),
                    main_string, bio_dates, mep_id, note_string
                )

    def get_queryset(self):
        return Person.objects.filter(
                Q(name__icontains=self.q) |
                Q(mep_id__icontains=self.q)
        )


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.people.models.Person` in nationalities many-to-many.
    '''

    def get_queryset(self):
        return Country.objects.filter(name__icontains=self.q)


class AddressAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.people.models.Person` in address many-to-many'''

    def get_queryset(self):
        '''
        Get queryset of :class:`mep.people.models.Addresss` objects.
        Use Q objects to search all relevant fields in autocomplete.
        '''
        # not searching lat or lon for now
        return Address.objects.filter(
            Q(name__icontains=self.q) |
            Q(street_address__icontains=self.q) |
            Q(city__icontains=self.q) |
            Q(postal_code__icontains=self.q) |
            Q(country__name__icontains=self.q) |
            Q(person__name__icontains=self.q)
        ).order_by('name', 'city', 'street_address')
