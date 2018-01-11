from dal import autocomplete
from django.contrib import admin
from django import forms

from mep.accounts.models import Account, AccountAddress, Subscription,\
    Reimbursement, Event, SubscriptionType
from mep.common.admin import NamedNotableAdmin, CollapsedTabularInline, \
    CollapsibleTabularInline


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


class SubscriptionAdminForm(forms.ModelForm):

    class Meta:
        model = Subscription
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


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    form = SubscriptionAdminForm
    date_hierarchy = 'start_date'
    list_display = ('account',  'category', 'subtype',
                    'duration', 'start_date', 'end_date',
                    'volumes', 'price_paid', 'deposit', 'currency_symbol')
    list_filter = ('category', 'subtype', 'currency')
    search_fields = ('account__persons__name', 'account__persons__mep_id', 'notes')
    fields = ('account', ('start_date', 'end_date'), 'subtype', 'category',
              'duration', 'volumes', 'deposit', 'price_paid', 'currency', 'notes')


class SubscriptionInline(CollapsibleTabularInline):
    model = Subscription
    form = SubscriptionAdminForm
    extra = 1
    fields = ('start_date', 'end_date', 'subtype', 'category', 'duration',
              'volumes', 'deposit', 'price_paid', 'currency', 'notes')


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

    def __init__(self, *args, **kwargs):
        super(ReimbursementAdminForm, self).__init__(*args, **kwargs)
        # override start date label to just date, since reimbursements
        # are single-day events
        self.fields['start_date'].label = "Date"


class ReimbursementAdmin(admin.ModelAdmin):
    form = ReimbursementAdminForm
    model = Reimbursement
    date_hierarchy = 'start_date'
    fields = ('account', ('start_date', 'refund', 'currency'), 'notes')
    list_display = ('account', 'date', 'refund', 'currency_symbol',)
    list_filter = ('currency',)
    search_fields = ('account__persons__name', 'account__persons__mep_id', 'notes')


class ReimbursementInline(CollapsibleTabularInline):
    model = Reimbursement
    form = ReimbursementAdminForm
    extra = 1
    fields = ('start_date', 'refund', 'currency', 'notes')


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
                        'data-minimum-input-length': 3,
                        'data-html': True
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
                    'data-minimum-input-length': 3,
                    'data-html': True
                }
            ),
        }


class EventAdmin(admin.ModelAdmin):
    '''Admin interface for the generic Events that underlie other subclasses
    such as Subscription and Reimbursment'''
    model = Event
    form = EventAdminForm
    date_hierarchy = 'start_date'
    fields = ('account', 'event_type', 'start_date', 'end_date', 'notes')
    readonly_fields = ('event_type',)
    list_display = ('account', 'event_type', 'start_date', 'end_date', 'notes')
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
    inlines = [AccountAddressInline, SubscriptionInline, ReimbursementInline]


class SubscriptionTypeAdmin(NamedNotableAdmin):
    list_display = ('name', 'notes')


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Reimbursement, ReimbursementAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(SubscriptionType, SubscriptionTypeAdmin)
