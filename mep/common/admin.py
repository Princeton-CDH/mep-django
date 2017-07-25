from django.contrib import admin


class NamedNotableAdmin(admin.ModelAdmin):
    '''Generic model admin for named/notable models.'''
    list_display = ('name', 'has_notes')
    # fields = ('name', 'notes')
    search_fields = ('name', 'notes')


class CollapsibleTabularInline(admin.TabularInline):
    'Django admin tabular inline with grappelli collapsible classes added'
    classes = ('grp-collapse grp-open',)

