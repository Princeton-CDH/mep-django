from django.conf.urls import url
from mep.books.views import ItemAutocomplete, ItemCSV


urlpatterns = [
    url(r'^items/autocomplete/$', ItemAutocomplete.as_view(),
        name='item-autocomplete'),
    url(r'^items/csv/$', ItemCSV.as_view(), name='items-csv'),
]
