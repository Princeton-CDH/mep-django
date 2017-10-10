from dal import autocomplete
from django.contrib import admin
from django import forms

from mep.accounts.models import Account, AccountAddress
from mep.common.admin import CollapsedTabularInline


class AccountAddressInlineForm(forms.ModelForm):
    class Meta:
        model = AccountAddress
        fields = ('__all__')
        widgets = {
                'address': autocomplete.ModelSelect2(
                    url='people:address-autocomplete',
                    attrs={
                        'data-placeholder': ('Type to search address data... '),
                        'data-minimum-input-length': 3
                    }
                ),
                'care_of_person': autocomplete.ModelSelect2(
                    url='people:autocomplete',
                    attrs={
                        'data-placeholder': ('Type to search for people...'),
                        'data-minimum-input-length': 3
                    }
                ),
        }


class AccountAddressInline(CollapsedTabularInline):
    model = AccountAddress
    form = AccountAddressInlineForm
    extra = 1
    fields = ('address', 'care_of_person', 'start_date', 'end_date', 'notes')


class AccountAdminForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ('__all__')
        widgets = {
            'persons': autocomplete.ModelSelect2Multiple(
                url='people:autocomplete',
                attrs={
                    'data-placeholder': ('Type to search for people...'),
                    'data-minimum-input-length': 3
                }
            ),
        }



class AccountAdmin(admin.ModelAdmin):
    model = Account
    form = AccountAdminForm
    list_display = ('id', 'list_persons', 'list_addresses')
    fields = ('persons',)
    inlines = [AccountAddressInline]


admin.site.register(Account, AccountAdmin)
