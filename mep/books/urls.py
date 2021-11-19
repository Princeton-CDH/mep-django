from django.urls import path

from mep.books import views

# url namespace
app_name = 'books'

urlpatterns = [
    path('books/', views.WorkList.as_view(), name='books-list'),
    path('books/autocomplete/', views.WorkAutocomplete.as_view(),
         name='work-autocomplete'),
    path('books/<slug:slug>/', views.WorkDetail.as_view(),
            name='book-detail'),
    path('books/<slug:slug>/circulation/',
            views.WorkCirculation.as_view(), name='book-circ'),
    path('books/<slug:slug>/cards/', views.WorkCardList.as_view(),
        name='book-card-list'),
]
