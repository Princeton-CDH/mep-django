from django.conf.urls import url
from mep.books.views import ItemAutocomplete

# url namespace
app_name = 'books'

urlpatterns = [
    url(r'^items/autocomplete/$', ItemAutocomplete.as_view(),
        name='item-autocomplete'),
]
