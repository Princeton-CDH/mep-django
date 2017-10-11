from django.conf.urls import url
from .views import AccountAutocomplete

urlpatterns = [
    url(r'^accounts/autocomplete/$', AccountAutocomplete.as_view(),
        name='autocomplete'),
]
