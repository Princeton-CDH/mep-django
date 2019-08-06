from django.conf.urls import url

from mep.books import views

# url namespace
app_name = 'books'

urlpatterns = [
    url(r'^books/$', views.WorkList.as_view(), name='books-list'),
    # TODO use something other than pk as a lookup for books
    url(r'^books/(?P<pk>\d+)/$', views.WorkDetail.as_view(), name='book-detail'),
    url(r'^books/autocomplete/$', views.WorkAutocomplete.as_view(),
        name='work-autocomplete'),
]
