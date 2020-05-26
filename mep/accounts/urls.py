from django.conf.urls import url

from mep.accounts.views import AccountAutocomplete, AddressList

# url namespace
app_name = 'accounts'

urlpatterns = [
    url(r'^accounts/addresses/$', AddressList.as_view()),
    url(r'^accounts/autocomplete/$', AccountAutocomplete.as_view(),
        name='autocomplete'),
]
