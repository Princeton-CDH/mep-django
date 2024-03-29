import re

from dal import autocomplete
from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.core.validators import RegexValidator

from mep.accounts.partial_date import PartialDateFormMixin
from mep.accounts.models import (
    Account,
    Address,
    Subscription,
    Reimbursement,
    Event,
    SubscriptionType,
    Borrow,
    Purchase,
)
from mep.books.models import Edition
from mep.common.admin import NamedNotableAdmin, CollapsibleTabularInline
from mep.footnotes.admin import FootnoteInline, AUTOCOMPLETE as footnote_autocomplete


# predefine autocomplete lookups (most are used on more than one form)
AUTOCOMPLETE = {
    "person": autocomplete.ModelSelect2(
        url="people:autocomplete",
        attrs={
            "data-placeholder": "Type to search for people...",
            "data-minimum-input-length": 3,
            "data-html": True,
        },
    ),
    "person-multiple": autocomplete.ModelSelect2Multiple(
        url="people:autocomplete",
        attrs={
            "data-placeholder": "Type to search for people...",
            "data-minimum-input-length": 3,
            "data-html": True,
        },
    ),
    "account": autocomplete.ModelSelect2(
        url="accounts:autocomplete",
        attrs={
            "data-placeholder": "Type to search for account...",
            "data-minimum-input-length": 3,
        },
    ),
    "location": autocomplete.ModelSelect2(
        url="people:location-autocomplete",
        attrs={
            "data-placeholder": "Type to search for location... ",
            "data-minimum-input-length": 3,
        },
    ),
    "work": autocomplete.ModelSelect2(
        url="books:work-autocomplete",
        attrs={
            "data-placeholder": "Type to search for work... ",
            "data-minimum-input-length": 3,
        },
    ),
}


class OpenFootnoteInline(FootnoteInline):
    """Customize footnote inline for borrowing and purchase events."""

    classes = ("grp-collapse",)  # grapelli collapsible, but not closed
    extra = 1


class SubEventFootnoteFormset(BaseGenericInlineFormSet):
    """'Custom inline formset for footnotes on non-geheric event classes.
    Find footnotes relative to the generic event instead of the subtable.
    """

    def __init__(self, instance=None, *args, **kwargs):
        if instance and hasattr(instance, "event_ptr"):
            # use base event object as model instance for retrieving footnotes
            instance = instance.event_ptr

        return super().__init__(instance=instance, *args, **kwargs)


class SubEventFootnoteInline(OpenFootnoteInline):
    """footnote line variant for subclasses of Events"""

    formset = SubEventFootnoteFormset


class EventEditionFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.work:
            self.fields["edition"].queryset = Edition.objects.filter(
                work=self.instance.work.pk
            )


class EventAdminForm(EventEditionFormMixin, PartialDateFormMixin):
    """Admin form for the Event model, adds autocomplete to account"""

    class Meta:
        model = Event
        fields = "__all__"
        help_texts = {
            "account": (
                "Searches and displays on system assigned "
                "account id, as well as associated person and "
                "address data."
            ),
        }
        widgets = {
            "account": AUTOCOMPLETE["account"],
            "work": AUTOCOMPLETE["work"],
        }


class EventTypeListFilter(admin.SimpleListFilter):
    """Filter that for :class:`~mep.accounts.models.Event` that can distinguish
    between event subtypes.
    """

    # human-readable title for filter
    title = "Event Type"

    # this gets used in the URL as a query param
    parameter_name = "event_type"

    def lookups(self, request, model_admin):
        # option tuples: left is query param name and right is human-readable name
        return (
            ("subscription", "Subscription"),
            ("reimbursement", "Reimbursement"),
            ("borrow", "Borrow"),
            ("purchase", "Purchase"),
            ("generic", "Generic"),
        )

    def queryset(self, request, queryset):
        # filter the queryset based on the selected option
        if self.value() == "generic":
            return queryset.generic()
        if self.value():
            # call the queryset filter method for the requested type
            # filter is named for event type + s
            return getattr(queryset, "%ss" % self.value())()

        # otherwise return unfilterd
        return queryset


class EventAdmin(admin.ModelAdmin):
    """Admin interface for the generic Events that underlie other subclasses
    such as Subscription and Reimbursment"""

    model = Event
    form = EventAdminForm
    date_hierarchy = "start_date"
    fields = (
        "account",
        "event_type",
        "partial_start_date",
        "partial_end_date",
        "work",
        "edition",
        "notes",
    )
    readonly_fields = ("event_type",)
    list_display = (
        "account",
        "event_type",
        "partial_start_date",
        "partial_end_date",
        "work",
        "notes",
    )
    search_fields = (
        "account__persons__name",
        "account__persons__mep_id",
        "start_date",
        "end_date",
        "notes",
        "work__title",
        "work__notes",
    )
    list_filter = (EventTypeListFilter,)
    inlines = [OpenFootnoteInline]


class SubscriptionAdminForm(PartialDateFormMixin):
    # regular expression to validate duration input and capture elements
    # for conversion into relativedelta; currently requires full names
    # and allows plural or singular
    duration_regex = re.compile(r"(?P<number>\d+)\s+(?P<unit>(day|week|month|year))s?")
    # validation error message
    duration_msg = (
        "Enter a number with one of day, week, month, or year "
        + " (singular or plural)."
    )

    # custom input field to allow users to view and enter human-readable
    # duration; used to calculate end date if start date and duration
    # are present but end date is not
    duration_units = forms.CharField(
        label="Duration",
        required=False,
        help_text="Duration in days, weeks, months, or years. "
        + "Enter as 1 day, 2 weeks, 3 months, 1 year, etc.",
        validators=[RegexValidator(regex=duration_regex, message=duration_msg)],
    )
    partial_purchase_date = forms.CharField(
        validators=[PartialDateFormMixin.partial_date_validator],
        required=False,
        help_text=PartialDateFormMixin.partial_date_help_text,
        label="Purchase date",
    )

    class Meta:
        model = Subscription
        fields = "__all__"
        help_texts = {
            "account": (
                "Searches and displays on system assigned "
                "account id, as well as associated person and "
                "address data."
            ),
            "end_date": (
                "Automatically calculated from start date and " "duration if not set."
            ),
        }
        widgets = {
            "account": AUTOCOMPLETE["account"],
        }

    def get_initial_for_field(self, field, field_name):
        # set initial value for duration units
        if field_name == "duration_units":
            return self.instance.readable_duration()
        if field_name == "partial_purchase_date":
            return self.instance.partial_purchase_date
        # handle everything else normally
        return super(SubscriptionAdminForm, self).get_initial_for_field(
            field, field_name
        )

    def clean(self):
        # if start date and duration are set, calculate end date
        cleaned_data = super(SubscriptionAdminForm, self).clean()
        # if invalid and unset, return
        if not cleaned_data:
            return
        # use bound subscription object to parse the dates
        subs = self.instance
        subs.partial_start_date = cleaned_data.get("partial_start_date", None)
        subs.partial_end_date = cleaned_data.get("partial_end_date", None)
        subs.partial_purchase_date = cleaned_data.get("partial_purchase_date", None)
        duration_units = cleaned_data.get("duration_units", None)
        if subs.partial_start_date and duration_units and not subs.partial_end_date:
            match = self.duration_regex.search(duration_units)
            duration_info = match.groupdict()
            unit = "%ss" % duration_info["unit"]  # ensure unit is plural
            value = int(duration_info["number"])
            # initialize relative delta, e.g. 2 months
            rel_duration = relativedelta(**{unit: value})
            # calculate end date based on start date (as date object)
            # and relative duration
            subs.end_date = subs.start_date + rel_duration
            # end date precision should be same as start
            subs.end_date_precision = subs.start_date_precision
            # set string value
            cleaned_data["partial_end_date"] = subs.partial_end_date

        return cleaned_data


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    form = SubscriptionAdminForm
    date_hierarchy = "start_date"
    list_display = (
        "account",
        "category",
        "subtype",
        "readable_duration",
        "duration",
        "partial_start_date",
        "partial_end_date",
        "partial_purchase_date",
        "volumes",
        "price_paid",
        "deposit",
        "currency_symbol",
    )
    list_filter = ("category", "subtype", "currency")
    search_fields = ("account__persons__name", "account__persons__mep_id", "notes")
    fields = (
        "account",
        ("partial_start_date", "partial_end_date", "partial_purchase_date"),
        "subtype",
        "category",
        "volumes",
        ("duration_units", "duration"),
        "deposit",
        "price_paid",
        "currency",
        "notes",
    )
    readonly_fields = ("duration",)
    inlines = (SubEventFootnoteInline,)


class SubscriptionInline(CollapsibleTabularInline):
    model = Subscription
    form = SubscriptionAdminForm
    extra = 1
    fields = (
        "partial_start_date",
        "partial_end_date",
        "partial_purchase_date",
        "subtype",
        "category",
        "volumes",
        "duration_units",
        "deposit",
        "price_paid",
        "currency",
        "notes",
    )


class ReimbursementAdminForm(PartialDateFormMixin):
    class Meta:
        model = Reimbursement
        fields = "__all__"
        help_texts = {
            "account": (
                "Searches and displays on system assigned "
                "account id, as well as associated person and "
                "address data."
            ),
        }
        widgets = {"account": AUTOCOMPLETE["account"]}

    def __init__(self, *args, **kwargs):
        super(ReimbursementAdminForm, self).__init__(*args, **kwargs)
        # override start date label to just date, since reimbursements
        # are single-day events
        self.fields["partial_start_date"].label = "Date"


class ReimbursementAdmin(admin.ModelAdmin):
    form = ReimbursementAdminForm
    model = Reimbursement
    date_hierarchy = "start_date"
    fields = ("account", ("partial_start_date", "refund", "currency"), "notes")
    list_display = (
        "account",
        "date",
        "refund",
        "currency_symbol",
    )
    list_filter = ("currency",)
    search_fields = ("account__persons__name", "account__persons__mep_id", "notes")
    inlines = (SubEventFootnoteInline,)


class PurchaseAdminForm(PartialDateFormMixin):
    class Meta:
        model = Purchase
        fields = ("account", "work", "partial_start_date", "price", "currency", "notes")
        help_texts = {
            "account": (
                "Searches and displays on system assigned "
                "account id, as well as associated person and "
                "address data."
            ),
        }
        widgets = {"account": AUTOCOMPLETE["account"], "work": AUTOCOMPLETE["work"]}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # override start date label to just date, since purchases
        # are single-day events
        self.fields["partial_start_date"].label = "Date"


class PurchaseAdmin(admin.ModelAdmin):
    form = PurchaseAdminForm
    date_hierarchy = "start_date"
    fields = ("account", "work", ("partial_start_date", "price", "currency"), "notes")
    list_display = (
        "account",
        "work",
        "edition",
        "date",
        "price",
        "currency_symbol",
    )
    list_filter = ("currency",)
    search_fields = ("account__persons__name", "account__persons__mep_id", "notes")
    inlines = (SubEventFootnoteInline,)


class PurchaseInline(CollapsibleTabularInline):
    model = Purchase
    form = PurchaseAdminForm
    extra = 1
    fields = ("work", ("partial_start_date", "price", "currency"), "notes")


class ReimbursementInline(CollapsibleTabularInline):
    model = Reimbursement
    form = ReimbursementAdminForm
    extra = 1
    fields = ("partial_start_date", "refund", "currency", "notes")


class AddressInlineForm(PartialDateFormMixin):
    class Meta:
        model = Address
        fields = "__all__"
        help_texts = {
            "account": (
                "Searches and displays on system assigned "
                "account id, as well as associated person and "
                "address data."
            ),
            "location": (
                "Searches on name, street address, city, " "postal code, and country."
            ),
        }
        widgets = {
            "account": AUTOCOMPLETE["account"],
            "location": AUTOCOMPLETE["location"],
            "person": AUTOCOMPLETE["person"],
            "care_of_person": AUTOCOMPLETE["person"],
        }


class AddressInline(CollapsibleTabularInline):
    # generic address edit - includes both account and person
    model = Address
    form = AddressInlineForm
    extra = 1
    fields = (
        "account",
        "person",
        "location",
        "partial_start_date",
        "partial_end_date",
        "care_of_person",
        "notes",
    )


class AccountAddressInline(AddressInline):
    # when associating a location with an account, don't allow editing
    # person
    fields = (
        "location",
        "partial_start_date",
        "partial_end_date",
        "care_of_person",
        "notes",
    )


class AccountAdminForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = "__all__"
        widgets = {
            "persons": AUTOCOMPLETE["person-multiple"],
            "card": footnote_autocomplete["bibliography"],
        }


class AccountAdmin(admin.ModelAdmin):
    model = Account
    form = AccountAdminForm
    list_display = (
        "id",
        "list_persons",
        "earliest_date",
        "last_date",
        "has_card",
        "list_locations",
    )
    search_fields = (
        "id",
        "address__location__street_address",
        "address__location__name",
        "address__location__country__name",
        "persons__name",
    )
    fields = ("persons", "card")
    inlines = [AccountAddressInline, SubscriptionInline, ReimbursementInline]

    class Media:
        js = ("admin/js/person-editlink.js",)


class SubscriptionTypeAdmin(NamedNotableAdmin):
    list_display = ("name", "notes")


class BorrowAdminForm(PartialDateFormMixin):
    class Meta:
        model = Borrow
        fields = (
            "account",
            "work",
            "item_status",
            "partial_start_date",
            "partial_end_date",
            "notes",
        )
        widgets = {
            "account": AUTOCOMPLETE["account"],
            "work": AUTOCOMPLETE["work"],
        }


class BorrowAdminListForm(forms.ModelForm):
    # custom form for list-editable item status on borrow list

    class Meta:
        model = Borrow
        exclude = []
        widgets = {"item_status": forms.RadioSelect}


class BorrowAdmin(admin.ModelAdmin):
    form = BorrowAdminForm
    list_display = (
        "account",
        "work",
        "edition",
        "partial_start_date",
        "partial_end_date",
        "item_status",
        "note_snippet",
    )
    date_hierarchy = "start_date"
    search_fields = (
        "account__persons__name",
        "account__persons__mep_id",
        "notes",
        "work__title",
        "work__notes",
    )
    list_filter = ("item_status", "work")
    list_editable = ("item_status",)
    fields = (
        "account",
        ("work", "item_status"),
        ("partial_start_date", "partial_end_date"),
        ("notes"),
    )
    inlines = (SubEventFootnoteInline,)

    class Media:
        js = ["admin/borrow-admin-list.js"]
        css = {"all": ["admin/borrow-admin-list.css"]}

    def get_changelist_form(self, request, **kwargs):
        # override the default changelist edit form in order to customize
        # widget for editing item status
        kwargs.setdefault("form", BorrowAdminListForm)
        return super(BorrowAdmin, self).get_changelist_form(request, **kwargs)


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Reimbursement, ReimbursementAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(SubscriptionType, SubscriptionTypeAdmin)
admin.site.register(Borrow, BorrowAdmin)
admin.site.register(Purchase, PurchaseAdmin)
