from django.urls import path

from mep.footnotes.views import BibliographyAutocomplete, CardList

# url namespace
app_name = "footnotes"

urlpatterns = [
    path(
        "bibliography/autocomplete/",
        BibliographyAutocomplete.as_view(),
        name="bibliography-autocomplete",
    ),
    path("cards/", CardList.as_view(), name="cards-list"),
]
