from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from viapy.widgets import ViafWidget

from mep.common.admin import NamedNotableAdmin, CollapsedTabularInline, \
    CollapsibleTabularInline
from mep.accounts.admin import AddressInline
from mep.footnotes.admin import FootnoteInline
from .models import Person, Country, Location, Profession, InfoURL, \
    Relationship, RelationshipType


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
            # special css class to customize django prepopulate behavior
            # opt out of slugify, don't prepopulate if there are spaces
            'sort_name': forms.TextInput(attrs={'class': 'prepopulate-noslug prepopulate-nospace'}),
        }


class PersonAddressInline(AddressInline):
    # extend address inline for person to specify foreign key field
    # and remove account from editable fields
    fields = ('location', 'start_date', 'end_date', 'care_of_person', 'notes')
    fk_name = 'person'


class PersonAdmin(admin.ModelAdmin):
    '''ModelAdmin for :class:`~mep.people.models.Person`.
    Uses custom template to display account subscription events and
    any relationships _to_ this person (only relationships to _other_
    people are edited here).
    '''
    form = PersonAdminForm
    list_display = ('name', 'title', 'sort_name', 'list_nationalities',
        'birth_year', 'death_year', 'sex', 'profession', 'viaf_id',
        'mep_id', 'address_count', 'in_logbooks', 'has_card', 'note_snippet')
    fields = ('mep_id', 'in_logbooks', 'title',
        ('name', 'sort_name'),
        'viaf_id',
        ('birth_year', 'death_year'),
        'sex', 'profession', 'nationalities', 'is_organization', 'notes')
    readonly_fields = ('mep_id', 'in_logbooks')
    search_fields = ('mep_id', 'name', 'sort_name', 'notes', 'viaf_id')
    list_filter = ('sex', 'profession', 'nationalities', 'is_organization')
    # Note: moving relationships to last for adjacency to list of relationships
    # *to* this person included in the template
    inlines = [InfoURLInline, PersonAddressInline, FootnoteInline, RelationshipInline]

    # by default, set sort name from name for those cases where
    # only one name is known and they are the same
    prepopulated_fields = {"sort_name": ("name",)}
    # NOTE: using a locally customized version of django's prepopulate.js
    # to allow using the prepopulate behavior without slugifying the value

    actions = ['merge_people']

    class Media:
        js = ['admin/viaf-lookup.js']

    def merge_people(self, request, queryset):
        '''Consolidate duplicate person records.'''
        # NOTE: using selected ids from form and ignoring queryset
        # because this action is only meant for use with a few
        # people at a time

        # Get any querystrings including filters, pickle them as a urlencoded
        # string
        request.session['people_merge_filter'] = urlencode(request.GET.items())
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        redirect = '%s?ids=%s' % (reverse('people:merge'), ','.join(selected))
        return HttpResponseRedirect(redirect, status=303)   # 303 = See Other
    merge_people.short_description = 'Merge selected people'


class LocationAdminForm(forms.ModelForm):
    '''Custom model form for Address editing.'''

    #: add a hidden field to pass in a mapbox access token from local settings
    mapbox_token = forms.CharField(initial=getattr(settings, 'MAPBOX_ACCESS_TOKEN', ''),
        widget=forms.HiddenInput)

    class Meta:
        model = Location
        exclude = []
        widgets = {
            'longitude': MapWidget
        }


class LocationAdmin(admin.ModelAdmin):
    form = LocationAdminForm
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
    inlines = [AddressInline, FootnoteInline]
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
admin.site.register(Location, LocationAdmin)
admin.site.register(Profession, NamedNotableAdmin)
admin.site.register(RelationshipType, NamedNotableAdmin)
