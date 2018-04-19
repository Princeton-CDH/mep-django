from django.contrib import admin

from mep.books.models import Item, Creator
from mep.common.admin import CollapsibleTabularInline


class ItemCreatorInline(CollapsibleTabularInline):
    # generic address edit - includes both account and person
    model = Creator
    # form = AddressInlineForm
    extra = 1
    fields = ('creator_type', 'person', 'notes')


class ItemAdmin(admin.ModelAdmin):
    list_display = ['mep_id', 'title', 'author_list', 'notes']
    inlines = [ItemCreatorInline]
    search_fields = ('mep_id', 'title', 'notes', 'creator__person__name')




admin.site.register(Item, ItemAdmin)
