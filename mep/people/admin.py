from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from viapy.widgets import ViafWidget

from mep.common.admin import NamedNotableAdmin, CollapsibleTabularInline
from mep.footnotes.admin import FootnoteInline
from .models import Person, Country, Address, Profession, InfoURL


class InfoURLInline(CollapsibleTabularInline):
    model = InfoURL
    fields = ('url', 'notes')


class GeoNamesLookupWidget(autocomplete.Select2):
    '''Customize autocomplete select widget to display Geonames URI
    as a link.'''

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'geonames-lookup'
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
    list_display = ('name', 'geonames_id')
    search_fields = ('name', 'geonames_id')
    fields = ['geonames_id', 'name']

    class Media:
        js = ['admin/geonames-lookup.js']


class ResidenceInline(CollapsibleTabularInline):
    model = Person.addresses.through


class PersonAdminForm(forms.ModelForm):
    '''Custom model form for Person editing; used to add VIAF lookup'''
    class Meta:
        model = Person
        exclude = []
        widgets = {
                'viaf_id': ViafWidget(
                    url='viaf:person-lookup',
                    attrs={
                        'data-placeholder': 'Type a name to search VIAF',
                        'data-minimum-input-length': 3
                    }
                )
        }


class PersonAdmin(admin.ModelAdmin):
    form = PersonAdminForm
    list_display = ('sort_name', 'name', 'birth_year', 'death_year',
        'sex', 'profession', 'viaf_id', 'mep_id', 'has_notes')
    fields = ('mep_id', 'title',
        ('name', 'sort_name'),
        'viaf_id',
        ('birth_year', 'death_year'),
        'sex', 'profession', 'nationalities', 'addresses',
        'notes')
    filter_horizontal = ('nationalities', 'addresses')
    readonly_fields = ('mep_id', )
    # FIXME: something is hiding VIAF url link. (grappelli maybe?)
    search_fields = ('mep_id', 'name', 'sort_name', 'notes')
    list_filter = ('sex', 'profession', 'nationalities')
    inlines = [InfoURLInline, FootnoteInline]


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
    fields = ('name', 'street_address', 'city', 'postal_code',
        'country',
        'latitude', 'longitude', 'mapbox_token',
        'notes')
    list_filter = ('country',)
    inlines = [ResidenceInline, FootnoteInline]
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