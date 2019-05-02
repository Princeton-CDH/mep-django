from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import Count, URLField
from django.utils.html import format_html
from django.utils.timezone import now
from tabular_export.admin import export_to_csv_response

from mep.accounts.admin import AUTOCOMPLETE
from mep.books.models import Creator, CreatorType, Item, Subject
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
    list_filter = ('genre', 'item_type')
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
                'notes', 'mep_id'
            )
        }),
        ('OCLC metadata', {
            'fields': (
                'uri', 'edition_uri', 'item_type', 'genre',
                'subject_list',

            )
        })
    )
    readonly_fields = ('mep_id', 'borrow_count', 'genre', 'subject_list')

    actions = ['export_to_csv']

    def get_queryset(self, request):
        '''Annotate the queryset with the number of borrows for sorting'''
        return super(ItemAdmin, self).get_queryset(request) \
                                     .annotate(Count('event__borrow'))

    def borrow_count(self, obj):
        '''Display the borrow count as a link to view associated borrows'''
        return format_html(
            '<a href="{0}?item__id__exact={1!s}" target="_blank">{2}</a>',
            reverse('admin:accounts_borrow_changelist'), str(obj.id),
            # use the database annotation rather than the object property
            # for efficiency
            obj.event__borrow__count
        )
    # use the annotated queryset value to make the field sortable
    borrow_count.admin_order_field = 'event__borrow__count'

    #: fields to be included in CSV export
    export_fields = ['admin_url', 'id', 'title', 'year', 'uri', 'author_list',
                     'mep_id', 'notes']

    def csv_filename(self):
        return 'mep-items-%s.csv' % now().strftime('%Y%m%dT%H:%M:%S')

    def tabulate_queryset(self, queryset):
        '''Generator for data in tabular form, including custom fields'''
        for item in queryset.prefetch_related('creator_set'):
            # retrieve values for configured export fields; if the attribute
            # is a callable (i.e., a custom property method), call it
            yield [value() if callable(value) else value
                   for value in (getattr(item, field) for field in self.export_fields)]

    def export_to_csv(self, request, queryset=None):
        '''Stream tabular data as a CSV file'''
        queryset = self.get_queryset(request) if queryset is None else queryset
        # use verbose names to label the columns (adapted from django-tabular-export)

        # get verbose names for model fields
        verbose_names = {i.name: i.verbose_name for i in queryset.model._meta.fields}

        # get verbose field name if there is one; look for verbose name
        # on a non-field attribute (e.g. a method); otherwise, title case the field name
        headers = [verbose_names.get(field, None) or
                   getattr(getattr(queryset.model, field), 'verbose_name', field.title())
                   for field in self.export_fields]

        return export_to_csv_response(self.csv_filename(), headers,
                                      self.tabulate_queryset(queryset))
    export_to_csv.short_description = 'Export selected items to CSV'

    def get_urls(self):
            # adds a custom URL for exporting all items as CSRF_FAILURE_VIEW = ''
        urls = [
            url(r'^csv/$', self.admin_site.admin_view(self.export_to_csv),
                name='books_item_csv')
        ]
        return urls + super(ItemAdmin, self).get_urls()


class CreatorTypeAdmin(admin.ModelAdmin):
    model = CreatorType
    list_display = ('name', 'notes')


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'uri', 'rdf_type')
    search_fields = ('name', 'uri', 'rdf_type')
    list_filter = ('rdf_type', )


admin.site.register(Item, ItemAdmin)
admin.site.register(CreatorType, CreatorTypeAdmin)
admin.site.register(Subject, SubjectAdmin)
