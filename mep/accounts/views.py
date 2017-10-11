from dal import autocomplete
from django.db.models import Q
from django.shortcuts import render
from .models import Account


class AccountAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.accounts.models.Account` in address many-to-many'''

    def get_queryset(self):
        '''Get a queryset filtered by query string. Searches on account id,
        people associated with account, and addresses associated with account
        '''

        return Account.objects.filter(
            Q(id__contains=self.q) |
            Q(persons__name__icontains=self.q) |
            Q(addresses__name__icontains=self.q) |
            Q(addresses__street_address__icontains=self.q) |
            Q(addresses__city__icontains=self.q)
        ).order_by('id')
