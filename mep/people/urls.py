from django.conf.urls import url

from mep.people import views

app_name = 'people'

urlpatterns = [
    url(r'^$', views.MembersList.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/$', views.MembersDetail.as_view(), name='detail'),
    url(r'^places/geonames/$', views.GeoNamesLookup.as_view(),
        name='geonames-lookup'),
    url(r'^places/geonames/country/$', views.GeoNamesLookup.as_view(),
        {'mode': 'country'}, name='country-lookup'),
    url(r'^people/autocomplete/$', views.PersonAutocomplete.as_view(),
        name='autocomplete'),
    url(r'^people/country/autocomplete', views.CountryAutocomplete.as_view(),
        name='country-autocomplete'),
    url(r'^people/location/autocomplete', views.LocationAutocomplete.as_view(),
        name='location-autocomplete'),
    url(r'^people/merge/$', views.PersonMerge.as_view(), name='merge'),
]
