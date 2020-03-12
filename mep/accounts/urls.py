from django.conf.urls import url

from mep.accounts.views import AccountAutocomplete

# url namespace
app_name = 'accounts'

urlpatterns = [
    url(r'^accounts/autocomplete/$', AccountAutocomplete.as_view(),
        name='autocomplete'),
]
