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
    list_display = ('id', 'title', 'author_list', 'notes', 'borrow_count')
    list_display_links = ('id', 'title')
    inlines = [ItemCreatorInline]
    search_fields = ('mep_id', 'title', 'notes', 'creator__person__name')
    fieldsets = (
        ('Basic metadata', {
            'fields': ('title', 'year', 'borrow_count')
        }),
        ('Additional metadata', {
            'fields': (
                # ('publishers', 'pub_places'),
                # ('volume'),
                'uri', 'notes', 'mep_id'
            )
        })
    )
    readonly_fields = ('mep_id', 'borrow_count')

    def get_queryset(self, request):
        '''Annotate the queryset with the number of borrows for sorting'''
        return super(ItemAdmin, self).get_queryset(request) \
                                     .annotate(Count('borrow'))

    def borrow_count(self, obj):
        '''Display the borrow count as a link to view associated borrows'''
        return format_html(
            '<a href="{0}?item__id__exact={1!s}" target="_blank">{2}</a>',
            reverse('admin:accounts_borrow_changelist'), str(obj.id),
            # use the database annotation rather than the object property
            # for efficiency
            obj.borrow__count
        )
    # use the annotated queryset value to make the field sortable
    borrow_count.admin_order_field = 'borrow__count'


class CreatorTypeAdmin(admin.ModelAdmin):
    model = CreatorType
    list_display = ('name', 'notes')


admin.site.register(Item, ItemAdmin)
admin.site.register(CreatorType, CreatorTypeAdmin)
