from django.conf.urls import url

from mep.people.views import GeoNamesLookup, PersonAutocomplete, \
    CountryAutocomplete, AddressAutocomplete


urlpatterns = [
    url(r'^places/geonames/$', GeoNamesLookup.as_view(),
        name='geonames-lookup'),
    url(r'^places/geonames/country/$', GeoNamesLookup.as_view(),
        {'mode': 'country'}, name='country-lookup'),
    url(r'^people/autocomplete/$', PersonAutocomplete.as_view(),
        name='autocomplete'),
    url(r'^people/country/autocomplete', CountryAutocomplete.as_view(),
        name='country-autocomplete'),
    url(r'^people/address/autocomplete', AddressAutocomplete.as_view(),
        name='address-autocomplete')

]
