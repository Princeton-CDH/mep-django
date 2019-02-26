from dal import autocomplete
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


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
    'bibliography': autocomplete.ModelSelect2(
        url='footnotes:bibliography-autocomplete',
        attrs={
            'data-placeholder': 'Type to search for bibliography... ',
        '   data-minimum-input-length': 3
        }
    ),
}



class NamedNotableAdmin(admin.ModelAdmin):
    '''Generic model admin for named/notable models.'''
    list_display = ('name', 'note_snippet')
    # fields = ('name', 'notes')
    search_fields = ('name', 'notes')


class CollapsibleTabularInline(admin.TabularInline):
    '''Django admin tabular inline with grappelli collapsible classes added'''
    classes = ('grp-collapse grp-open',)


class CollapsedTabularInline(admin.TabularInline):
    '''
    Django admin tabular inline with grappelli collapsible classes added,
    defaulting to collapsed.
    '''
    classes = ('grp-collapse grp-closed',)


class LocalUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('is_superuser', 'is_active',
        'last_login', 'group_names')

    def group_names(self, obj):
        '''custom property to display group membership'''
        if obj.groups.exists():
            return ', '.join(g.name for g in obj.groups.all())
    group_names.short_description = 'groups'


admin.site.unregister(User)
admin.site.register(User, LocalUserAdmin)
