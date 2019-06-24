from django.conf.urls import url
from mep.footnotes.views import BibliographyAutocomplete

# url namespace
app_name = 'footnotes'

urlpatterns = [
    url(r'^bibliography/autocomplete/$', BibliographyAutocomplete.as_view(),
        name='bibliography-autocomplete'),
]
