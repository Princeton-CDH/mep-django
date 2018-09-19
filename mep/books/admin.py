from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.utils.html import format_html
from tabular_export.core import get_field_names_from_queryset
from tabular_export.admin import export_to_csv_response

from mep.accounts.admin import AUTOCOMPLETE
from mep.books.models import Creator, CreatorType, Item
from mep.common.admin import CollapsibleTabularInline


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
    list_display = ('id', 'title', 'author_list', 'notes', 'borrow_count',
                    'updated_at')
    list_display_links = ('id', 'title')
    inlines = [ItemCreatorInline]
    search_fields = ('mep_id', 'title', 'notes', 'creator__person__name', 'id')
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
    actions = ('export_to_csv',)

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

    def tabular_headers(self, queryset):
        '''Get the headers for exported tabular data, including custom fields'''
        return get_field_names_from_queryset(queryset) + ['authors', 'url']

    def tabulate_queryset(self, queryset):
        '''Generator for item data in tabular form, including custom fields'''
        fields = get_field_names_from_queryset(queryset)
        for item in queryset.prefetch_related('creator_set'):
            values = [getattr(item, field) for field in fields]
            values.extend((item.author_list(),
                           reverse('admin:books_item_change', args=[item.id])))
            yield values

    def export_to_csv(self, request, queryset):
        '''Stream tabular data as a CSV file'''
        return export_to_csv_response('items.csv',
                                      self.tabular_headers(queryset),
                                      self.tabulate_queryset(queryset))
    export_to_csv.short_description = 'Export selected items to CSV'


class CreatorTypeAdmin(admin.ModelAdmin):
    model = CreatorType
    list_display = ('name', 'notes')


admin.site.register(Item, ItemAdmin)
admin.site.register(CreatorType, CreatorTypeAdmin)
