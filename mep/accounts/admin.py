from dal import autocomplete
from django.contrib import admin
from django import forms

from mep.accounts.models import Account, AccountAddress, Subscribe,\
    Reimbursement, Event
from mep.common.admin import CollapsedTabularInline


class EventAdminForm(forms.ModelForm):
    '''Admin form for the Event model, adds autocomplete to account'''
    class Meta:
        model = Event
        fields = ('__all__')
        help_texts = {
            'account': ('Searches and displays on system assigned '
                        'account id, as well as associated person and '
                        'address data.'),
        }
        widgets = {
            'account': autocomplete.ModelSelect2(
                url='accounts:autocomplete',
                attrs={
                    'data-placeholder': 'Type to search account data...',
                    'data-minimum-input-length': 3
                }
            ),
        }


class SubscribeAdminForm(forms.ModelForm):

    class Meta:
        model = Subscribe
        fields = ('__all__')
        help_texts = {
            'account': ('Searches and displays on system assigned '
                        'account id, as well as associated person and '
                        'address data.'),
        }
        widgets = {
            'account': autocomplete.ModelSelect2(
                url='accounts:autocomplete',
                attrs={
                    'data-placeholder': 'Type to search account data...',
                    'data-minimum-input-length': 3
                }
            ),
        }


class ReimbursementAdminForm(forms.ModelForm):
    class Meta:
        model = Reimbursement
        fields = ('__all__')
        help_texts = {
            'account': ('Searches and displays on system assigned '
                        'account id, as well as associated person and '
                        'address data.'),
        }
        widgets = {
            'account': autocomplete.ModelSelect2(
                url='accounts:autocomplete',
                attrs={
                    'data-placeholder': 'Type to search account data...',
                    'data-minimum-input-length': 3
                }
            ),
        }


class ReimbursementAdmin(admin.ModelAdmin):
    form = ReimbursementAdminForm
    model = Reimbursement
    fields = ('account', 'price', 'currency', 'start_date', 'end_date', 'notes')
    list_display = ('account', 'price', 'currency', 'start_date', 'end_date',)
    list_filter = ('currency',)
    search_fields = ('account__persons__name', 'account__persons__mep_id')


class SubscribeAdmin(admin.ModelAdmin):
    model = Subscribe
    form = SubscribeAdminForm
    list_display = ('account', 'sub_type', 'modification',
                    'duration', 'start_date', 'end_date',
                    'volumes', 'price_paid', 'deposit', 'currency')
    list_filter = ('sub_type', 'modification', 'currency')

    fields = ('account', 'sub_type', 'modification', 'duration', 'start_date',
              'end_date', 'volumes', 'price_paid', 'deposit', 'currency', 'notes')


class ReimbursementInline(CollapsedTabularInline):
    model = Reimbursement
    form = ReimbursementAdminForm
    extra = 1
    fields = ('price', 'currency', 'start_date', 'end_date', 'notes')


class SubscribeInline(CollapsedTabularInline):
    model = Subscribe
    form = SubscribeAdminForm
    extra = 1
    fields = ('sub_type', 'modification', 'duration', 'start_date', 'end_date', 'volumes', 'price_paid', 'deposit',
              'currency', 'notes')


class AccountAddressInlineForm(forms.ModelForm):
    class Meta:
        model = AccountAddress
        fields = ('__all__')
        help_texts = {
            'account': ('Searches and displays on system assigned '
                        'account id, as well as associated person and '
                        'address data.'),
            'address': ('Searches on address name, street address, city, '
                        'postal code, and country.'),

        }
        widgets = {
                'account': autocomplete.ModelSelect2(
                    url='accounts:autocomplete',
                    attrs={
                        'data-placeholder': 'Type to search account data...',
                        'data-minimum-input-length': 3
                    }
                ),
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
    fields = ('account', 'address', 'care_of_person', 'start_date', 'end_date', 'notes')


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


class EventAdmin(admin.ModelAdmin):
    '''Admin interface for the generic Events that underlie other subclasses
    such as Subscribe and Reimbursment'''
    model = Subscribe
    form = EventAdminForm
    date_hierarchy = 'start_date'
    fields = ('account', 'event_type', 'start_date', 'end_date', 'notes')
    readonly_fields = ('event_type',)
    list_display = ('account', 'start_date', 'end_date', 'notes', 'event_type')
    search_fields = ('account__persons__name', 'account__persons__mep_id',
                     'start_date', 'end_date', 'notes')


class AccountAdmin(admin.ModelAdmin):
    model = Account
    form = AccountAdminForm
    list_display = ('id', 'list_persons', 'list_addresses')
    search_fields = ('id', 'accountaddress__address__street_address',
                     'accountaddress__address__name',
                     'accountaddress__address__country__name', 'persons__name')
    fields = ('persons',)
    inlines = [AccountAddressInline, SubscribeInline, ReimbursementInline]


admin.site.register(Subscribe, SubscribeAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Reimbursement, ReimbursementAdmin)
admin.site.register(Event, EventAdmin)
