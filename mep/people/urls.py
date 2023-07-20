from django.urls import path, re_path

from mep.people import views

# url namespace
app_name = "people"

urlpatterns = [
    # public member urls
    path("members/", views.MembersList.as_view(), name="members-list"),
    path("members/graphs/", views.MembershipGraphs.as_view(), name="member-graphs"),
    re_path(
        r"^members/(?P<slug>[\w-]+)/$",
        views.MemberDetail.as_view(),
        name="member-detail",
    ),
    re_path(
        r"^members/(?P<slug>[\w-]+)/membership/$",
        views.MembershipActivities.as_view(),
        name="membership-activities",
    ),
    re_path(
        r"^members/(?P<slug>[\w-]+)/borrowing/$",
        views.BorrowingActivities.as_view(),
        name="borrowing-activities",
    ),
    re_path(
        r"^members/(?P<slug>[\w-]+)/cards/$",
        views.MemberCardList.as_view(),
        name="member-card-list",
    ),
    re_path(
        r"^members/(?P<slug>[\w-]+)/cards/(?P<short_id>[\w-]+)/$",
        views.MemberCardDetail.as_view(),
        name="member-card-detail",
    ),
    # admin urls
    path("places/geonames/", views.GeoNamesLookup.as_view(), name="geonames-lookup"),
    path(
        "places/geonames/country/",
        views.GeoNamesLookup.as_view(),
        {"mode": "country"},
        name="country-lookup",
    ),
    path(
        "people/autocomplete/", views.PersonAutocomplete.as_view(), name="autocomplete"
    ),
    path(
        "people/country/autocomplete",
        views.CountryAutocomplete.as_view(),
        name="country-autocomplete",
    ),
    path(
        "people/location/autocomplete",
        views.LocationAutocomplete.as_view(),
        name="location-autocomplete",
    ),
    path("people/merge/", views.PersonMerge.as_view(), name="merge"),
]
