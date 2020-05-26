from dal import autocomplete
from django.conf import settings
from django.db.models import Q
from django.views.generic.base import ContextMixin

from .models import Account, Location


class AddressMapMixin(ContextMixin):
    '''Adds values from local settings used to render leaflet address maps to 
    the view, along with the address info for the library itself.'''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # add local settings values for basemaps & mapbox access token
        context.update({
            'mapbox_token': getattr(settings, 'MAPBOX_ACCESS_TOKEN', ''),
            'mapbox_basemap': getattr(settings, 'MAPBOX_BASEMAP', ''),
            'paris_overlay': getattr(settings, 'PARIS_OVERLAY', ''),
        })

        # address of the lending library itself; automatically available from
        # migration mep/people/migrations/0014_library_location.py
        try:
            library = Location.objects.get(name='Shakespeare and Company')
            context['library_address'] = {
                'name': library.name,
                'street_address': library.street_address,
                'city': library.city,
                'latitude': str(library.latitude),
                'longitude': str(library.longitude),
            }
        except Location.DoesNotExist:
            # if we can't find library's address send 'null' & don't render it
            context['library_address'] = None

        return context


class AccountAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.accounts.models.Account` in address many-to-many'''

    def get_queryset(self):
        '''Get a queryset filtered by query string. Searches on account id,
        people associated with account, and addresses associated with account
        '''

        return Account.objects.filter(
            Q(id__contains=self.q) |
            Q(persons__name__icontains=self.q) |
            Q(persons__mep_id__icontains=self.q) |
            Q(locations__name__icontains=self.q) |
            Q(locations__street_address__icontains=self.q) |
            Q(locations__city__icontains=self.q)
        ).distinct().order_by('id')
