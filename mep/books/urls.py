from django.conf.urls import url
from mep.books.views import ItemAutocomplete

urlpatterns = [
    url(r'^items/autocomplete/$', ItemAutocomplete.as_view(),
        name='item-autocomplete'),
]
