from django.conf.urls import url

from mep.books import views

# url namespace
app_name = 'books'

urlpatterns = [
    url(r'^books/$', views.WorkList.as_view(), name='books-list'),
    url(r'^books/autocomplete/$', views.WorkAutocomplete.as_view(),
        name='work-autocomplete'),
    url(r'^books/(?P<slug>[\w-]+)/$', views.WorkDetail.as_view(),
        name='book-detail'),
    url(r'^books/(?P<slug>[\w-]+)/circulation$', views.WorkCirculation.as_view(),
        name='book-circ'),
]
