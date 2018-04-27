import re

from dal import autocomplete
from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib import admin
from django.core.validators import RegexValidator

from mep.accounts.models import Account, Address, Subscription,\
    Reimbursement, Event, SubscriptionType, Borrow, PartialDate
from mep.common.admin import NamedNotableAdmin, CollapsibleTabularInline
from mep.footnotes.admin import FootnoteInline


# predefine autocomplete lookups (most are used on more than one form)
AUTOCOMPLETE = {
    'person': autocomplete.ModelSelect2(url='people:autocomplete',
        attrs={
            'data-placeholder': 'Type to search for people...',
            'data-minimum-input-length': 3,
            'data-html': True
        }
    ),
    'person-multiple': autocomplete.ModelSelect2Multiple(
        url='people:autocomplete',
        attrs={
            'data-placeholder': 'Type to search for people...',
            'data-minimum-input-length': 3,
            'data-html': True
        }
    ),
    'account': autocomplete.ModelSelect2(url='accounts:autocomplete',
        attrs={
            'data-placeholder': 'Type to search for account...',
            'data-minimum-input-length': 3
        }
    ),
    'location': autocomplete.ModelSelect2(url='people:location-autocomplete',
        attrs={
            'data-placeholder': 'Type to search for location... ',
            'data-minimum-input-length': 3
        }
    ),
    'item': autocomplete.ModelSelect2(url='books:item-autocomplete',
        attrs={
            'data-placeholder': 'Type to search for item... ',
            'data-minimum-input-length': 3
        }
    ),
}

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
            'account': AUTOCOMPLETE['account'],
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


class SubscriptionAdminForm(forms.ModelForm):
    # regular expression to validate duration input and capture elements
    # for conversion into relativedelta; currently requires full names
    # and allows plural or singular
    duration_regex = re.compile(r'(?P<number>\d+)\s+(?P<unit>(day|week|month|year))s?')
    # validation error message
    duration_msg = "Enter a number with one of day, week, month, or year " + \
        " (singular or plural)."

    # custom input field to allow users to view and enter human-readable
    # duration; used to calculate end date if start date and duration
    # are present but end date is not
    duration_units = forms.CharField(label='Duration', required=False,
        help_text='Duration in days, weeks, months, or years. ' + \
                  'Enter as 1 day, 2 weeks, 3 months, 1 year, etc.',
        validators=[RegexValidator(regex=duration_regex,
                                   message=duration_msg)
                    ]
        )

    class Meta:
        model = Subscription
        fields = ('__all__')
        help_texts = {
            'account': ('Searches and displays on system assigned '
                        'account id, as well as associated person and '
                        'address data.'),
            'end_date': ('Automatically calculated from start date and '
                         'duration if not set.')
        }
        widgets = {
            'account': AUTOCOMPLETE['account'],
        }

    def get_initial_for_field(self, field, field_name):
        # set initial value for duration units
        if field_name == 'duration_units':
            return self.instance.readable_duration()
        # handle everything else normally
        return super(SubscriptionAdminForm, self).get_initial_for_field(field, field_name)

    def clean(self):
        cleaned_data = super(SubscriptionAdminForm, self).clean()
        # if start date and duration are set, calculate end date
        start_date = cleaned_data.get('start_date', None)
        end_date = cleaned_data.get('end_date', None)
        duration_units = cleaned_data.get('duration_units', None)
        if start_date and duration_units and not end_date:
            match = self.duration_regex.search(duration_units)
            duration_info = match.groupdict()
            unit = '%ss' % duration_info['unit']  # ensure unit is plural
            value = int(duration_info['number'])
            # initialize relative delta, e.g. 2 months
            rel_duration = relativedelta(**{unit: value})
            cleaned_data['end_date'] = start_date + rel_duration

        return cleaned_data


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    form = SubscriptionAdminForm
    date_hierarchy = 'start_date'
    list_display = ('account', 'category', 'subtype',
                    'readable_duration', 'duration', 'start_date', 'end_date',
                    'volumes', 'price_paid', 'deposit', 'currency_symbol')
    list_filter = ('category', 'subtype', 'currency')
    search_fields = ('account__persons__name', 'account__persons__mep_id', 'notes')
    fields = ('account', ('start_date', 'end_date'), 'subtype', 'category',
              'volumes', ('duration_units', 'duration'),
              'deposit', 'price_paid',
              'currency', 'notes')
    readonly_fields = ('duration',)


class SubscriptionInline(CollapsibleTabularInline):
    model = Subscription
    form = SubscriptionAdminForm
    extra = 1
    fields = ('start_date', 'end_date', 'subtype', 'category', 'volumes',
              'duration_units', 'deposit', 'price_paid', 'currency', 'notes')


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


class AddressInlineForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('__all__')
        help_texts = {
            'account': ('Searches and displays on system assigned '
                        'account id, as well as associated person and '
                        'address data.'),
            'location': ('Searches on name, street address, city, '
                        'postal code, and country.'),
        }
        widgets = {
            'account': AUTOCOMPLETE['account'],
            'location': AUTOCOMPLETE['location'],
            'person': AUTOCOMPLETE['person'],
            'care_of_person': AUTOCOMPLETE['person'],
        }


class AddressInline(CollapsibleTabularInline):
    # generic address edit - includes both account and person
    model = Address
    form = AddressInlineForm
    extra = 1
    fields = ('account', 'person', 'location', 'start_date', 'end_date',
              'care_of_person', 'notes')

class AccountAddressInline(AddressInline):
    # when associating a location with an account, don't allow editing
    # person
    fields = ('location', 'start_date', 'end_date', 'care_of_person', 'notes')


class AccountAdminForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ('__all__')
        widgets = {
            'persons': AUTOCOMPLETE['person-multiple'],
         }


class AccountAdmin(admin.ModelAdmin):
    model = Account
    form = AccountAdminForm
    list_display = ('id', 'list_persons', 'earliest_date', 'last_date',
                    'has_card', 'list_locations')
    search_fields = ('id', 'address__location__street_address',
                     'address__location__name',
                     'address__location__country__name', 'persons__name')
    fields = ('persons', 'card')
    inlines = [AccountAddressInline, SubscriptionInline, ReimbursementInline]

    class Media:
        js = ("admin/js/person-editlink.js",)


class SubscriptionTypeAdmin(NamedNotableAdmin):
    list_display = ('name', 'notes')


class BorrowAdminForm(forms.ModelForm):
    partial_date_validator = RegexValidator(
        regex=PartialDate.partial_date_re,
        message="Value is not a recognized date."
    )
    partial_date_help_text = "Enter as much of the date as known, in any of the \
        following formats: yyyy, yyyy-mm, yyyy-mm-dd, --mm-dd"
    partial_start_date = forms.CharField(validators=[partial_date_validator],
        required=False, help_text=partial_date_help_text, label="Start date")
    partial_end_date = forms.CharField(validators=[partial_date_validator],
        required=False, help_text=partial_date_help_text, label="End date")

    class Meta:
        model = Borrow
        fields = ('account', 'item', 'partial_start_date', 'partial_end_date',
            'notes')
        widgets = {
            'account': AUTOCOMPLETE['account'],
            'item': AUTOCOMPLETE['item']
        }

    def get_initial_for_field(self, field, name):
        if name == 'partial_start_date':
            return self.instance.partial_start_date
        if name == 'partial_end_date':
            return self.instance.partial_end_date
        return super(BorrowAdminForm, self).get_initial_for_field(field, name)

    def clean(self):
        '''Parse partial dates and save them on form submission.'''
        cleaned_data = super(BorrowAdminForm, self).clean()
        if not self.errors:
            self.instance.partial_start_date = cleaned_data['partial_start_date']
            self.instance.partial_end_date = cleaned_data['partial_end_date']
            return cleaned_data

class BorrowFootnoteInline(FootnoteInline):
    # customize standard footnote inline for borrowing event footnote
    classes = ('grp-collapse', )  # grapelli collapsible, but not closed
    fields = ('bibliography', 'location', 'notes')
    extra = 0


class BorrowAdmin(admin.ModelAdmin):
    form = BorrowAdminForm
    list_display = ('account', 'item', 'partial_start_date', 'partial_end_date',
        'item_status', 'note_snippet')
    date_hierarchy = 'start_date'
    search_fields = ('account__persons__name', 'account__persons__mep_id',
        'notes', 'item__title', 'item__notes')
    list_filter = ('item_status',)
    list_editable = ('item_status',)
    fields = (
        ('account', 'item'),
        ('partial_start_date', 'partial_end_date'),
        ('notes')
    )
    inlines = (BorrowFootnoteInline, )


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Reimbursement, ReimbursementAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(SubscriptionType, SubscriptionTypeAdmin)
admin.site.register(Borrow, BorrowAdmin)

