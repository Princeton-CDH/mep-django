from django.contrib import admin

from mep.common.admin import NamedNotableAdmin, CollapsibleTabularInline
from mep.footnotes.admin import FootnoteInline
from .models import Person, Country, Address, Profession, InfoURL


class InfoURLInline(CollapsibleTabularInline):
    model = InfoURL
    fields = ('url', 'notes')


class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


class ResidenceInline(CollapsibleTabularInline):
    model = Person.addresses.through


class PersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'birth_year', 'death_year',
        'sex', 'profession', 'viaf_id', 'mep_id', 'has_notes')
    fields = ('mep_id', 'title',
        ('last_name', 'first_name'),
        'viaf_id',
        ('birth_year', 'death_year'),
        'sex', 'profession', 'nationalities', 'addresses',
        'notes')
    filter_horizontal = ('nationalities', 'addresses')
    readonly_fields = ('mep_id', )
    # FIXME: something is hiding VIAF url link. (grappelli maybe?)
    search_fields = ('mep_id', 'first_name', 'last_name', 'notes')
    list_filter = ('sex', 'profession', 'nationalities')
    inlines = [InfoURLInline, FootnoteInline]


class AddressAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'address_line_1', 'address_line_2', 'city_town',
        'country', 'has_notes')
    fields = ('address_line_1', 'address_line_2', 'city_town', 'postal_code',
        'country',
        ('latitude', 'longitude'),
        'notes')
    list_filter = ('country',)
    inlines = [ResidenceInline, FootnoteInline]


# enable default admin to see imported data
admin.site.register(Person, PersonAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Profession, NamedNotableAdmin)