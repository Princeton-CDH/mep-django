from django.conf.urls import url

from mep.people.views import GeoNamesLookup, PersonAutocomplete


urlpatterns = [
    url(r'^places/geonames/$', GeoNamesLookup.as_view(),
        name='geonames-lookup'),
    url(r'^places/geonames/country/$', GeoNamesLookup.as_view(),
        {'mode': 'country'}, name='country-lookup'),
    url(r'^people/autocomplete/$', PersonAutocomplete.as_view(),
        name='autocomplete'),

]
