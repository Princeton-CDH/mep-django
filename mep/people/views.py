from django.db.models import Q
from django.http import JsonResponse
from dal import autocomplete

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
    '''Basic person autocomplete lookup, for use with
    django-autocomplete-light.'''

    def get_queryset(self):
        return Person.objects.filter(name__icontains=self.q)


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.people.models.Person` in nationalities many-to-many.'''

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
            Q(country__name__icontains=self.q)
        )
