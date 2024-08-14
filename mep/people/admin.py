import logging
import os
import csv
from functools import cached_property

from dal import autocomplete
from django import forms
from django.conf import settings
from django.db import IntegrityError
from django.urls import path, reverse
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from import_export.resources import ModelResource
from import_export.widgets import ManyToManyWidget, Widget
from import_export.fields import Field
from tabular_export.admin import export_to_csv_response
from viapy.widgets import ViafWidget

from mep.accounts.admin import AddressInline
from mep.common.admin import (
    CollapsedTabularInline,
    CollapsibleTabularInline,
    NamedNotableAdmin,
)
from mep.footnotes.admin import FootnoteInline
from mep.common.admin import ImportExportModelResource, LocalImportExportModelAdmin
from mep.people.models import (
    Country,
    InfoURL,
    Location,
    Person,
    Profession,
    Relationship,
    RelationshipType,
)


logger = logging.getLogger(__name__)


class InfoURLInline(CollapsibleTabularInline):
    model = InfoURL
    fields = ("url", "notes")


class GeoNamesLookupWidget(autocomplete.Select2):
    """Customize autocomplete select widget to display Geonames URI
    as a link."""

    def render(self, name, value, renderer=None, attrs=None):
        if attrs is None:
            attrs = {}
        attrs["class"] = "geonames-lookup"
        # select2 filters based on existing choices (non-existent here),
        # so when a value is set, add it to the list of choices
        if value:
            self.choices = [(value, value)]
        widget = super(GeoNamesLookupWidget, self).render(name, value, attrs)
        return mark_safe(
            ('%s<p><a id="geonames_uri" target="_blank" href="%s">%s</a></p>')
            % (widget, value or "", value or "")
        )


class MapWidget(forms.NumberInput):
    """Customize numeric input and add a map div to display a leaflet map
    for latitude and longitude values on the form."""

    def render(self, name, value, renderer=None, attrs=None):
        widget = super(MapWidget, self).render(name, value, attrs)
        return mark_safe('<div id="geonames_map"></div>%s' % widget)


class CountryAdminForm(forms.ModelForm):
    """Custom model form for Place editing, used to add geonames lookup."""

    #: add a hidden field to pass in a mapbox access token from local settings
    # mapbox_token = forms.CharField(initial=getattr(settings, 'MAPBOX_ACCESS_TOKEN', ''),
    # widget=forms.HiddenInput)

    class Meta:
        model = Country
        exclude = []
        widgets = {
            "geonames_id": GeoNamesLookupWidget(
                url="people:country-lookup",
                attrs={
                    "data-placeholder": "Type location name to search...",
                    "data-minimum-input-length": 3,
                },
            )
        }


class CountryAdmin(admin.ModelAdmin):
    form = CountryAdminForm
    list_display = ("name", "geonames_id", "code")
    search_fields = ("name", "geonames_id", "code")
    fields = ["geonames_id", "name", "code"]

    class Media:
        js = ["admin/geonames-lookup.js"]


class RelationshipInlineForm(forms.ModelForm):
    """Custom model form for Book editing, used to add autocomplete
    for place lookup."""

    class Meta:
        model = Relationship
        # Setting a logical order for the relationship fields
        fields = ("relationship_type", "to_person", "notes")
        widgets = {
            "to_person": autocomplete.ModelSelect2(
                url="people:autocomplete",
                attrs={
                    "data-placeholder": ("Start typing name/mep_id to " "search...")
                },
            )
        }


class RelationshipInline(CollapsedTabularInline):
    """Inline class for Relationships"""

    model = Relationship
    fk_name = "from_person"
    form = RelationshipInlineForm
    verbose_name_plural = "Relationships"
    extra = 1


class PersonAdminForm(forms.ModelForm):
    """Custom model form for Person editing; used to add VIAF lookup"""

    class Meta:
        model = Person
        fields = "__all__"
        widgets = {
            "viaf_id": ViafWidget(
                url="viaf:person-search",
                attrs={
                    "data-placeholder": "Type name or id to search VIAF",
                    "data-minimum-input-length": 3,
                },
            ),
            "nationalities": autocomplete.ModelSelect2Multiple(
                url="people:country-autocomplete",
                attrs={
                    "data-placeholder": ("Type a country name to search... "),
                    "data-minimum-input-length": 3,
                },
            ),
            # special css class to customize django prepopulate behavior
            # opt out of slugify, don't prepopulate if there are spaces
            "sort_name": forms.TextInput(
                attrs={"class": "prepopulate-noslug prepopulate-nospace"}
            ),
        }

    # NOTE: overriding Django's prepopulate.js with a local version that honors
    # the custom classes for sort_name behavior. Explicitly including
    # because when Django is not running in DEBUG mode it loads
    # a minified version instead of the local override
    class Media:
        js = ("admin/js/prepopulate.js",)


class PersonTypeListFilter(admin.SimpleListFilter):
    """Filter that for :class:`~mep.people.models.Person` that can distinguish
    between people who are creators of books vs. those who are library members.
    """

    # human-readable title for filter
    title = "Person Type"

    # this gets used in the URL as a query param
    parameter_name = "person_type"

    def lookups(self, request, model_admin):
        # option tuples: left is query param name and right is human-readable name
        return (
            ("creator", "Creator"),
            ("member", "Library Member"),
            ("uncategorized", "Uncategorized"),
        )

    def queryset(self, request, queryset):
        # filter the queryset based on the selected option
        if self.value() == "creator":  # is creator
            return queryset.exclude(creator=None)
        if self.value() == "member":  # has account
            return queryset.exclude(account=None)
        if self.value() == "uncategorized":  # no account or creator
            return queryset.filter(account=None).filter(creator=None)


class PersonAdmin(admin.ModelAdmin):
    """ModelAdmin for :class:`~mep.people.models.Person`.
    Uses custom template to display account subscription events and
    any relationships _to_ this person (only relationships to _other_
    people are edited here).
    """

    form = PersonAdminForm
    list_display = (
        "name",
        "title",
        "sort_name",
        "list_nationalities",
        "birth_year",
        "death_year",
        "gender",
        "profession",
        "viaf_id",
        "mep_id",
        "account_id",
        "address_count",
        "in_logbooks",
        "has_card",
        "verified",
        "updated_at",
        "note_snippet",
    )
    fields = (
        "title",
        ("name", "sort_name"),
        ("slug", "mep_id"),
        ("has_account", "in_logbooks", "has_card", "is_creator"),
        "viaf_id",
        ("birth_year", "death_year", "viaf_date_override"),
        "gender",
        "profession",
        "nationalities",
        "is_organization",
        "verified",
        "notes",
        "public_notes",
        "past_slugs_list",
    )
    readonly_fields = (
        "mep_id",
        "in_logbooks",
        "has_account",
        "has_card",
        "is_creator",
        "past_slugs_list",
    )
    search_fields = (
        "mep_id",
        "name",
        "sort_name",
        "notes",
        "public_notes",
        "viaf_id",
        "slug",
    )
    list_filter = (
        PersonTypeListFilter,
        "gender",
        "profession",
        "nationalities",
        "is_organization",
    )
    # Note: moving relationships to last for adjacency to list of relationships
    # *to* this person included in the template
    inlines = [InfoURLInline, FootnoteInline, RelationshipInline]

    # by default, set sort name from name for those cases where
    # only one name is known and they are the same
    prepopulated_fields = {"sort_name": ("name",), "slug": ("sort_name",)}
    # NOTE: using a locally customized version of django's prepopulate.js
    # to allow using the prepopulate behavior without slugifying the value

    actions = ["merge_people", "export_to_csv"]

    class Media:
        js = ["admin/viaf-lookup.js"]

    def merge_people(self, request, queryset):
        """Consolidate duplicate person records."""
        # NOTE: using selected ids from form and ignoring queryset
        # because this action is only meant for use with a few
        # people at a time

        # Get any querystrings including filters, pickle them as a urlencoded
        # string
        request.session["people_merge_filter"] = urlencode(request.GET.items())
        selected = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
        redirect = "%s?ids=%s" % (reverse("people:merge"), ",".join(selected))
        return HttpResponseRedirect(redirect, status=303)  # 303 = See Other

    merge_people.short_description = "Merge selected people"
    merge_people.allowed_permissions = ("change", "delete")

    #: fields to be included in CSV export
    export_fields = [
        "id",
        "name",
        "sort_name",
        "mep_id",
        "account_id",
        "birth_year",
        "death_year",
        "gender",
        "title",
        "profession",
        "is_organization",
        "is_creator",
        "has_account",
        "in_logbooks",
        "has_card",
        "subscription_dates",
        "verified",
        "updated_at",
        "admin_url",
        "viaf_id",
    ]

    def csv_filename(self):
        """Generate filename for CSV download"""
        return "mep-people-%s.csv" % now().strftime("%Y%m%dT%H:%M:%S")

    def tabulate_queryset(self, queryset):
        """Generator for data in tabular form, including custom fields"""
        prefetched = queryset.prefetch_related(
            "account_set",
            "creator_set",
            "account_set__event_set",
            "account_set__event_set__subscription",
        ).select_related("profession")
        for person in prefetched:
            # retrieve values for configured export fields; if the attribute
            # is a callable (i.e., a custom property method), call it
            yield [
                value() if callable(value) else value
                for value in (getattr(person, field) for field in self.export_fields)
            ]

    def export_to_csv(self, request, queryset=None):
        """Stream tabular data as a CSV file"""
        queryset = self.get_queryset(request) if queryset is None else queryset

        # use verbose names to label the columns (adapted from django-tabular-export)
        # get verbose names for model fields
        verbose_names = {i.name: i.verbose_name for i in queryset.model._meta.fields}
        # get verbose field name if there is one; look for verbose name
        # on a non-field attribute (e.g. a method); otherwise, title case the field name
        headers = [
            verbose_names.get(field, None)
            or getattr(
                getattr(queryset.model, field),
                "verbose_name",
                field.replace("_", " ").title(),
            )
            for field in self.export_fields
        ]
        return export_to_csv_response(
            self.csv_filename(), headers, self.tabulate_queryset(queryset)
        )

    export_to_csv.short_description = "Export selected people to CSV"

    def get_urls(self):
        """Return admin urls; adds a custom URL for exporting all people
        as CSV"""
        urls = [
            path(
                "csv/",
                self.admin_site.admin_view(self.export_to_csv),
                name="people_person_csv",
            )
        ]
        return urls + super(PersonAdmin, self).get_urls()

    def past_slugs_list(self, instance=None):
        """list of previous slugs for this person, for read-only display"""
        if instance:
            return ", ".join([p.slug for p in instance.past_slugs.all()])

    past_slugs_list.short_description = "Past slugs"
    past_slugs_list.long_description = "Alternate slugs from edits or merges"


class LocationAdminForm(forms.ModelForm):
    """Custom model form for Address editing."""

    #: add a hidden field to pass in a mapbox access token from local settings
    mapbox_token = forms.CharField(
        initial=getattr(settings, "MAPBOX_ACCESS_TOKEN", ""), widget=forms.HiddenInput
    )

    class Meta:
        model = Location
        exclude = []
        widgets = {"longitude": MapWidget}


class LocationAdmin(admin.ModelAdmin):
    form = LocationAdminForm
    list_display = ("__str__", "name", "street_address", "city", "country", "has_notes")
    # Use fieldset in order to add more instructions for looking up
    # the geographic coordinates
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "street_address",
                    "city",
                    "postal_code",
                    "country",
                    "notes",
                )
            },
        ),
        (
            "Geographic Coordinates",
            {
                "fields": ("latitude", "longitude", "mapbox_token"),
                "description": mark_safe(
                    'Use <a href="http://www.latlong.net/" target="_blank">http://www.latlong.net/</a>'
                    + " to find coordinates for an address.  Confirm using this map, "
                    + "which will update whenever the coordinates are modified."
                ),
            },
        ),
    )

    list_filter = ("country",)
    search_fields = ("name", "street_address", "city", "notes")
    inlines = [AddressInline, FootnoteInline]

    class Media:
        css = {
            "all": [
                "https://unpkg.com/leaflet@1.0.2/dist/leaflet.css",
                "admin/geonames.css",
            ]
        }
        js = [
            "admin/geonames-lookup.js",
            "https://unpkg.com/leaflet@1.0.2/dist/leaflet.js",
        ]


PERSON_IMPORT_COLUMNS = ("slug", "gender", "nationalities")

PERSON_IMPORT_EXPORT_COLUMNS = (
    "slug",
    "name",
    "birth_year",
    "death_year",
    "gender",
    "nationalities",
    "notes",
    "mep_id",
    "sort_name",
    "viaf_id",
    "is_organization",
    "verified",
    "title",
    "profession",
    "public_notes",
    "updated_at",
)


class ExportPersonResource(ModelResource):
    nationalities = Field(
        attribute="nationalities",
        widget=ManyToManyWidget(Country, field="name", separator=";"),
    )

    class Meta:
        model = Person
        fields = PERSON_IMPORT_EXPORT_COLUMNS
        export_order = PERSON_IMPORT_EXPORT_COLUMNS
        chunk_size = 1000


class PersonResource(ImportExportModelResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        # run shared mep.common import/export steps
        super().before_import(dataset, using_transactions, dry_run, **kwargs)

        # identify and create any new countries for nationalities
        nationalities = {
            nat.strip()
            for row in dataset.dict
            for nat in row["nationalities"].split(";")
            if nat.strip()
        }
        known_countries = (
            Country.objects.filter(name__in=nationalities)
            .distinct("name")
            .values_list("name", flat=True)
        )
        unknown_countries = nationalities - set(known_countries)
        try:
            countries = Country.objects.bulk_create(
                [Country(name=nat) for nat in unknown_countries]
            )
            logger.debug(
                f"Successfully created records for {len(countries)} new countries"
            )
        except IntegrityError as e:
            logger.debug(
                f"Database integrity error occurred in creating new countries: {e}"
            )
        except Exception as e:
            logger.debug(f"Error occurred in creating new countries: {e}")

    def before_import_row(self, row, **kwargs):
        """
        Called on an OrderedDictionary of row attributes.
        Opportunity to do quick string formatting as a
        principle of charity to annotators before passing
        values into django-import-export lookup logic.
        """
        # make sure slug is valid and matches
        self.validate_row_by_slug(row)

        # gender to one char
        gstr = str(row.get("gender")).strip()
        row["gender"] = gstr[0].upper() if gstr else ""

    # Use many-to-many widget to separate and import nationalities
    nationalities = Field(
        column_name="nationalities",
        attribute="nationalities",
        widget=ManyToManyWidget(Country, field="name", separator=";"),
    )

    class Meta:
        model = Person
        fields = PERSON_IMPORT_COLUMNS
        import_id_fields = ("slug",)
        export_order = PERSON_IMPORT_COLUMNS
        skip_unchanged = True
        report_skipped = True
        store_instance = True


class PersonAdminImportExport(PersonAdmin, LocalImportExportModelAdmin):
    resource_classes = [PersonResource]

    def get_export_resource_classes(self):
        """
        Use a distinct resource class for exporting,
        since export and import have support different fields
        """
        return [ExportPersonResource]

    def get_queryset(self, request):
        # add prefetching so admin list display and export will be faster
        return (
            super()
            .get_queryset(request)
            .select_related("profession")
            .prefetch_related(
                "nationalities",
                "account_set",
                "account_set__locations",
                "account_set__persons",
            )
        )


# enable default admin to see imported data
admin.site.register(Person, PersonAdminImportExport)
admin.site.register(Country, CountryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Profession, NamedNotableAdmin)
admin.site.register(RelationshipType, NamedNotableAdmin)
