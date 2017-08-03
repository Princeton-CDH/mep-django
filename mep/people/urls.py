from django.conf.urls import url

from mep.people.views import GeonamesLookup


urlpatterns = [
    url(r'^places/geonames/$', GeonamesLookup.as_view(),
        name='geonames-lookup'),
    url(r'^places/geonames/country/$', GeonamesLookup.as_view(),
        {'mode': 'country'}, name='country-lookup'),

]
