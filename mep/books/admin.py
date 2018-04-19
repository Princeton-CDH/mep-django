from django.contrib import admin
from django import forms

from mep.books.models import Item, Creator
from mep.common.admin import CollapsibleTabularInline
from mep.accounts.admin import AUTOCOMPLETE


class ItemCreatorInlineForm(forms.ModelForm):
    class Meta:
        model = Creator
        fields = ('creator_type', 'person', 'notes')
        widgets = {
            'person': AUTOCOMPLETE['person'],
        }


class ItemCreatorInline(CollapsibleTabularInline):
    # generic address edit - includes both account and person
    model = Creator
    form = ItemCreatorInlineForm
    extra = 1


class ItemAdmin(admin.ModelAdmin):
    list_display = ['mep_id', 'title', 'author_list', 'notes']
    inlines = [ItemCreatorInline]
    search_fields = ('mep_id', 'title', 'notes', 'creator__person__name')
    fieldsets = (
        ('Basic metadata', {
            'fields': ('title', 'mep_id', 'year')
        }),
        ('Additional metadata', {
            'fields': (
                # ('publishers', 'pub_places'),
                # ('volume'),
                ('uri'),
                ('notes')
            )
        })
    )
    readonly_fields = ('mep_id',)


admin.site.register(Item, ItemAdmin)