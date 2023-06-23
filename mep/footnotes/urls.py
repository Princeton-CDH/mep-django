from django.conf.urls import url

from mep.footnotes.views import BibliographyAutocomplete, CardList

# url namespace
app_name = "footnotes"

urlpatterns = [
    url(
        r"^bibliography/autocomplete/$",
        BibliographyAutocomplete.as_view(),
        name="bibliography-autocomplete",
    ),
    url(r"^cards/$", CardList.as_view(), name="cards-list"),
]
