from django.contrib import admin

from .models import Person, Country, Address

class PersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'birth_year', 'death_year',
        'sex', 'profession', 'viaf_id', 'mep_id', 'has_notes')
    fields = ('mep_id', 'title',
        ('last_name', 'first_name'),
        'viaf_id',
        ('birth_year', 'death_year'),
        'sex', 'profession', 'nationalities',
        'notes')
    filter_horizontal = ('nationalities', )
    readonly_fields = ('mep_id', )
    search_fields = ('mep_id', 'first_name', 'last_name', 'notes')
    list_filter = ('sex', 'profession', 'nationalities')


# enable default admin to see imported data
admin.site.register(Person, PersonAdmin)
admin.site.register(Country)
admin.site.register(Address)