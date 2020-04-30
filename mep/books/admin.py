from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.core.validators import ValidationError
from django.urls import reverse
from django.db.models import Count
from django.utils.html import format_html
from django.utils.timezone import now

from tabular_export.admin import export_to_csv_response

from mep.accounts.admin import AUTOCOMPLETE
from mep.accounts.partial_date import PartialDateFormMixin
from mep.books.models import Creator, CreatorType, Work, Subject, Format, \
    Genre, Edition
from mep.books.queryset import WorkSolrQuerySet
from mep.common.admin import CollapsibleTabularInline


class WorkCreatorInlineForm(forms.ModelForm):
    class Meta:
        model = Creator
        fields = ('creator_type', 'person', 'order', 'notes')
        widgets = {
            'person': AUTOCOMPLETE['person'],
        }


class WorkCreatorInline(CollapsibleTabularInline):
    # generic address edit - includes both account and person
    model = Creator
    form = WorkCreatorInlineForm
    extra = 1


class EditionForm(forms.ModelForm):
    class Meta:
        model = Edition
        fields = ('title', 'partial_date',
                  'volume', 'number', 'season', 'edition',
                  'uri', 'notes')

    partial_date = forms.CharField(
        validators=[PartialDateFormMixin.partial_date_validator],
        required=False,
        help_text='%s; used to sort editions and display year. %s' % (
            Edition._meta.get_field('date').help_text,
            PartialDateFormMixin.partial_date_help_text),
        label="Date")

    def get_initial_for_field(self, field, name):
        if name == 'partial_date':
            return self.instance.partial_date
        return super().get_initial_for_field(field, name)

    def clean(self):
        '''Parse partial dates and save them on form submission.'''
        cleaned_data = super().clean()
        if not self.errors:
            try:
                self.instance.partial_date = cleaned_data['partial_date']
            except ValueError as verr:
                raise ValidationError('Date validation error: %s' % verr)
            return cleaned_data


class EditionInline(admin.StackedInline):
    model = Edition
    form = EditionForm
    extra = 1
    show_change_link = True
    classes = ('grp-collapse grp-open',)
    fields = (
        'title', 'partial_date',
        ('volume', 'number', 'season', 'edition'),
        'uri', 'notes'
    )


class WorkAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'display_title', 'author_list', 'notes',
        'events', 'borrows', 'purchases',
        'updated_at', 'has_uri')
    list_display_links = ('id', 'display_title')
    list_filter = ('genres', 'work_format')
    inlines = [EditionInline, WorkCreatorInline]
    # NOTE: admin search uses Solr, actual fields configured in solrconfig.xml
    # but search fields must be defined for search to be turned on
    search_fields = ('mep_id', 'title', 'notes', 'public_notes',
                     'creator__person__name', 'id', 'slug')
    fieldsets = (
        ('Basic metadata', {
            'fields': ('title', 'year', 'sort_title',
                       ('events', 'borrows', 'purchases'),
                       'slug')
        }),
        ('Additional metadata', {
            'fields': (
                'notes', 'public_notes', 'ebook_url', 'mep_id'
            )
        }),
        ('OCLC metadata', {
            'fields': (
                'uri', 'edition_uri', 'work_format',
                'genres',
                'subjects',
            )
        })
    )
    readonly_fields = ('mep_id', 'events', 'borrows', 'purchases',
                       'sort_title')
    filter_horizontal = ('genres', 'subjects')

    actions = ['export_to_csv']

    def get_queryset(self, request):
        '''Annotate the queryset with the number of events, borrows,
        and purchases for sorting and display.'''
        return super(WorkAdmin, self) \
            .get_queryset(request).count_events()

    def get_search_results(self, request, queryset, search_term):
        '''Override admin search to use Solr.'''

        # if search term is not blank, filter the queryset via solr search
        if search_term:
            # - use AND instead of OR to get smaller result sets, more
            #  similar to default admin search behavior
            # - return pks for all matching records
            sqs = WorkSolrQuerySet().search_admin_work(search_term) \
                .raw_query_parameters(**{'q.op': 'AND'}) \
                .only('pk') \
                .get_results(rows=100000)

            pks = [r['pk'] for r in sqs]
            # filter queryset by id if there are results
            if sqs:
                queryset = queryset.filter(pk__in=pks)
            else:
                queryset = queryset.none()

        # return queryset, use distinct not needed
        return queryset, False

    def _event_count(self, obj, event_type='event'):
        '''Display an event count as a link to associated event.
        Takes an optional event type to allow displaying and linking to
        event types (i.e. borrow or purchase).'''
        admin_link_url = 'admin:accounts_%s_changelist' % event_type
        # use the database annotation rather than the object property
        # for efficiency
        count_attr = 'event__%scount' % \
            ('%s__' % event_type if event_type != 'event' else '')
        return format_html(
            '<a href="{0}?work__id__exact={1!s}" target="_blank">{2}</a>',
            reverse(admin_link_url), str(obj.id),
            getattr(obj, count_attr)
        )

    def display_title(self, obj):
        '''Display actual title, but sort on sort title'''
        return obj.title
    display_title.admin_order_field = 'sort_title'
    display_title.short_description = 'title'

    def events(self, obj):
        '''Display total event count as a link to view associated events'''
        return self._event_count(obj)
    # use the annotated queryset value to make the field sortable
    events.admin_order_field = 'event__count'

    def borrows(self, obj):
        '''Display the borrow count as a link to view associated borrows'''
        return self._event_count(obj, 'borrow')
    # use the annotated queryset value to make the field sortable
    borrows.admin_order_field = 'event__borrow__count'

    def purchases(self, obj):
        '''Display the purchase count as a link to view associated purchases'''
        return self._event_count(obj, 'purchase')
    # use the annotated queryset value to make the field sortable
    purchases.admin_order_field = 'event__purchase__count'

    #: fields to be included in CSV export
    export_fields = [
        'admin_url', 'id', 'slug', 'title', 'year', 'author_list', 'mep_id',
        'uri', 'edition_uri', 'genre_list', 'format', 'subject_list',
        'event_count', 'borrow_count', 'purchase_count',
        'notes'
    ]

    def csv_filename(self):
        return 'mep-works-%s.csv' % now().strftime('%Y%m%dT%H:%M:%S')

    def tabulate_queryset(self, queryset):
        '''Generator for data in tabular form, including custom fields'''

        # prefetch creators to speed up bulk processing
        # annotate with event counts for inclusion (needed in case
        # queryset was generated from a search and doesn't get default logic)
        queryset = queryset.prefetch_related('creator_set') \
                           .count_events()

        for work in queryset:
            # retrieve values for configured export fields; if the attribute
            # is a callable (i.e., a custom property method), call it
            yield [value() if callable(value) else value
                   for value in (getattr(work, field) for field
                                 in self.export_fields)]

    def export_to_csv(self, request, queryset=None):
        '''Stream tabular data as a CSV file'''
        queryset = self.get_queryset(request) if queryset is None else queryset
        # use verbose names to label the columns
        # (adapted from django-tabular-export)

        # get verbose names for model fields
        verbose_names = {
            i.name: i.verbose_name for i in queryset.model._meta.fields
        }
        # add verbose names for event counts
        verbose_names.update({
            'event_count': 'Events', 'borrow_count': 'Borrows',
            'purchase_count': 'Purchases'
        })

        # get verbose field name if there is one; look for verbose name
        # on a non-field attribute (e.g. a method); otherwise,
        # title case the field name
        headers = [verbose_names.get(field, None) or
                   getattr(getattr(queryset.model, field),
                           'verbose_name', field.title())
                   for field in self.export_fields]

        return export_to_csv_response(self.csv_filename(), headers,
                                      self.tabulate_queryset(queryset))
    export_to_csv.short_description = 'Export selected works to CSV'

    def get_urls(self):
        # adds a custom URL for exporting all items as CSRF_FAILURE_VIEW = ''
        urls = [
            url(r'^csv/$', self.admin_site.admin_view(self.export_to_csv),
                name='books_work_csv')
        ]
        return urls + super(WorkAdmin, self).get_urls()


class CreatorTypeAdmin(admin.ModelAdmin):
    model = CreatorType
    list_display = ('name', 'notes', 'order')
    list_editable = ('order',)


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'uri', 'rdf_type')
    search_fields = ('name', 'uri', 'rdf_type')
    list_filter = ('rdf_type', )


class FormatAdmin(admin.ModelAdmin):
    list_display = ('name', 'uri')
    # override default order to put notes last
    fields = ('name', 'uri', 'notes')


admin.site.register(Work, WorkAdmin)
admin.site.register(CreatorType, CreatorTypeAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Format, FormatAdmin)
admin.site.register(Genre)

# NOTE: edition needs to be registered to allow adding from event
# edit form; allow editing not inline?
# admin.site.register(Edition)
