from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from viapy.widgets import ViafWidget

from mep.common.admin import NamedNotableAdmin, CollapsibleTabularInline, CollapsedTabularInline
from mep.accounts.admin import AccountAddressInline
from mep.footnotes.admin import FootnoteInline
from .models import Person, Country, Address, Profession, InfoURL, \
    Relationship, RelationshipType


class InfoURLInline(CollapsedTabularInline):
    model = InfoURL
    fields = ('url', 'notes')


class GeoNamesLookupWidget(autocomplete.Select2):
    '''Customize autocomplete select widget to display Geonames URI
    as a link.'''

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'geonames-lookup'
        # select2 filters based on existing choices (non-existent here),
        # so when a value is set, add it to the list of choices
        if value:
            self.choices = [(value, value)]
        widget = super(GeoNamesLookupWidget, self).render(name, value, attrs)
        return mark_safe((u'%s<p><a id="geonames_uri" target="_blank" href="%s">%s</a></p>') % \
            (widget, value or '', value or ''))


class MapWidget(forms.NumberInput):
    '''Customize numeric input and add a map div to display a leaflet map
    for latitude and longitude values on the form.'''

    def render(self, name, value, attrs=None):
        widget = super(MapWidget, self).render(name, value, attrs)
        return mark_safe(u'<div id="geonames_map"></div>%s' % widget)


class CountryAdminForm(forms.ModelForm):
    '''Custom model form for Place editing, used to add geonames lookup.'''

    #: add a hidden field to pass in a mapbox access token from local settings
    # mapbox_token = forms.CharField(initial=getattr(settings, 'MAPBOX_ACCESS_TOKEN', ''),
        # widget=forms.HiddenInput)

    class Meta:
        model = Country
        exclude = []
        widgets = {
            'geonames_id': GeoNamesLookupWidget(url='people:country-lookup',
                attrs={'data-placeholder': 'Type location name to search...',
                       'data-minimum-input-length': 3})
        }


class CountryAdmin(admin.ModelAdmin):
    form = CountryAdminForm
    list_display = ('name', 'geonames_id', 'code')
    search_fields = ('name', 'geonames_id', 'code')
    fields = ['geonames_id', 'name', 'code']

    class Media:
        js = ['admin/geonames-lookup.js']


class ResidenceInline(CollapsedTabularInline):
    model = Person.addresses.through


class RelationshipInlineForm(forms.ModelForm):
    '''Custom model form for Book editing, used to add autocomplete
    for place lookup.'''
    class Meta:
        model = Relationship
        # Setting a logical order for the relationship fields
        fields = ('relationship_type', 'to_person', 'notes')
        widgets = {
            'to_person': autocomplete.ModelSelect2(
                url='people:autocomplete',
                attrs={'data-placeholder': ('Start typing name/mep_id to '
                                            'search...')}
            )
        }


class RelationshipInline(CollapsedTabularInline):
    '''Inline class for Relationships'''
    model = Relationship
    fk_name = 'from_person'
    form = RelationshipInlineForm
    verbose_name_plural = 'Relationships'
    extra = 1


class PersonAdminForm(forms.ModelForm):
    '''Custom model form for Person editing; used to add VIAF lookup'''
    class Meta:
        model = Person
        fields = ('__all__')
        widgets = {
                'viaf_id': ViafWidget(
                    url='viaf:person-search',
                    attrs={
                        'data-placeholder': 'Type name or id to search VIAF',
                        'data-minimum-input-length': 3
                    }
                ),
                'nationalities': autocomplete.ModelSelect2Multiple(
                    url='people:country-autocomplete',
                    attrs={
                        'data-placeholder': ('Type a country name to search... '),
                        'data-minimum-input-length': 3
                    }
                ),
                'addresses': autocomplete.ModelSelect2Multiple(
                    url='people:address-autocomplete',
                    attrs={
                        'data-placeholder': ('Type to search address data... '),
                        'data-minimum-input-length': 3
                    }
                )
        }


class PersonAdmin(admin.ModelAdmin):
    # NOTE: uses custom template to display relationships to this person
    # (only relationships to other people are edited here)
    form = PersonAdminForm
    list_display = ('name', 'title', 'sort_name', 'list_nationalities', 'birth_year', 'death_year',
        'sex', 'profession', 'viaf_id', 'mep_id', 'address_count', 'has_account', 'note_snippet')
    fields = ('mep_id', 'has_account', 'title',
        ('name', 'sort_name'),
        'viaf_id',
        ('birth_year', 'death_year'),
        'sex', 'profession', 'nationalities', 'addresses',
        'notes')
    readonly_fields = ('mep_id', 'has_account')
    search_fields = ('mep_id', 'name', 'sort_name', 'notes', 'viaf_id')
    list_filter = ('sex', 'profession', 'nationalities')
    inlines = [InfoURLInline, RelationshipInline, FootnoteInline]

    class Media:
        js = ['admin/viaf-lookup.js']


class AddressAdminForm(forms.ModelForm):
    '''Custom model form for Address editing.'''

    #: add a hidden field to pass in a mapbox access token from local settings
    mapbox_token = forms.CharField(initial=getattr(settings, 'MAPBOX_ACCESS_TOKEN', ''),
        widget=forms.HiddenInput)

    class Meta:
        model = Address
        exclude = []
        widgets = {
            'longitude': MapWidget
        }


class AddressAdmin(admin.ModelAdmin):
    form = AddressAdminForm
    list_display = ('__str__', 'name', 'street_address', 'city',
        'country', 'has_notes')
    # Use fieldset in order to add more instructions for looking up
    # the geographic coordinates
    fieldsets = (
        (None, {
            'fields': ('name', 'street_address', 'city', 'postal_code',
                       'country', 'notes')
            }),
        ('Geographic Coordinates', {
            'fields': ('latitude', 'longitude', 'mapbox_token'),
            'description':
            mark_safe('Use <a href="http://www.latlong.net/" target="_blank">http://www.latlong.net/</a>' +
                ' to find coordinates for an address.  Confirm using this map, ' +
                'which will update whenever the coordinates are modified.'),
            }),
    )

    list_filter = ('country',)
    search_fields = ('name', 'street_address', 'city', 'notes')
    inlines = [AccountAddressInline, ResidenceInline, FootnoteInline]
    class Media:
        css = {
            'all': ['https://unpkg.com/leaflet@1.0.2/dist/leaflet.css',
                    'admin/geonames.css']
        }
        js = ['admin/geonames-lookup.js',
             'https://unpkg.com/leaflet@1.0.2/dist/leaflet.js']



# enable default admin to see imported data
admin.site.register(Person, PersonAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Profession, NamedNotableAdmin)
admin.site.register(RelationshipType, NamedNotableAdmin)
