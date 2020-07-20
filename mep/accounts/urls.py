from django.conf.urls import url

from mep.accounts.views import AccountAutocomplete, Twitter100yearsReview

# url namespace
app_name = 'accounts'

urlpatterns = [
    url(r'^accounts/autocomplete/$', AccountAutocomplete.as_view(),
        name='autocomplete'),
    url(r'^events/100-years-review/$', Twitter100yearsReview.as_view()),
]
