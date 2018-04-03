from django.contrib import admin

from mep.books.models import Item

class ItemAdmin(admin.ModelAdmin):
    list_display = ['mep_id', 'title', 'notes']


admin.site.register(Item, ItemAdmin)
