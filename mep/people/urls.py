from django.conf.urls import url

from mep.people import views

# url namespace
app_name = 'people'

urlpatterns = [
    url(r'^members/$', views.MembersList.as_view(), name='members-list'),
    # TODO use something other than pk as a lookup for members
    url(r'^members/(?P<pk>\d+)/$', views.MemberDetail.as_view(), name='member-detail'),
    url(r'^members/(?P<pk>\d+)/activities/$',
        views.MembershipActivities.as_view(), name='membership-activities'),
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