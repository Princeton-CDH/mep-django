from django.conf.urls import url
from mep.books.views import ItemAutocomplete, ItemList

# url namespace
app_name = 'books'

urlpatterns = [
    url(r'^books/$', ItemList.as_view(), name='books-list'),
    # TODO use something other than pk as a lookup for books
    url(r'^items/autocomplete/$', ItemAutocomplete.as_view(),
        name='item-autocomplete'),
]
