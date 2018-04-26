from django.contrib import admin
from django import forms
from django.db.models import Count
from django.utils.html import format_html
from django.core.urlresolvers import reverse

from mep.books.models import Item, Creator, CreatorType
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
    list_display = ['mep_id', 'title', 'author_list', 'notes', 'borrow_count']
    inlines = [ItemCreatorInline]
    search_fields = ('mep_id', 'title', 'notes', 'creator__person__name')
    fieldsets = (
        ('Basic metadata', {
            'fields': ('title', 'year', 'mep_id', 'borrow_count')
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
    readonly_fields = ('mep_id', 'borrow_count')

    def get_queryset(self, request):
        '''Annotate the queryset with the number of borrows for sorting'''
        qs = super(ItemAdmin, self).get_queryset(request)
        qs = qs.annotate(Count('borrow'))
        return qs

    def borrow_count(self, obj):
        '''Display the borrow count as a link to view associated borrows'''
        return format_html(
            '<a href="{}">{}</a>',
            # TODO make this more elegant?
            reverse('admin:accounts_borrow_changelist') + '?item__id__exact=' + str(obj.id),
            obj.borrow_count # this is the property, not the annotation
        )

    # use the annotated queryset value to make the field sortable
    borrow_count.admin_order_field = 'borrow__count'


class CreatorTypeAdmin(admin.ModelAdmin):
    model = CreatorType
    list_display = ('name', 'notes')


admin.site.register(Item, ItemAdmin)
admin.site.register(CreatorType, CreatorTypeAdmin)
