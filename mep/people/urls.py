from django.conf.urls import url

from mep.people.views import GeoNamesLookup


urlpatterns = [
    url(r'^places/geonames/$', GeoNamesLookup.as_view(),
        name='geonames-lookup'),
    url(r'^places/geonames/country/$', GeoNamesLookup.as_view(),
        {'mode': 'country'}, name='country-lookup'),

]
