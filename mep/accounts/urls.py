from django.urls import path

from mep.accounts.views import AccountAutocomplete, Twitter100yearsReview

# url namespace
app_name = 'accounts'

urlpatterns = [
    path('accounts/autocomplete/', AccountAutocomplete.as_view(),
        name='autocomplete'),
    path('events/100-years-review/', Twitter100yearsReview.as_view()),
]
