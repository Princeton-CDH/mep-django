from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from mep.common.admin import NamedNotableAdmin
from .models import SourceType, Bibliography, Footnote


class FootnoteAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'bibliography', 'location', 'is_agree')
    list_filter = ('bibliography__source_type', 'content_type')
    CONTENT_LOOKUP_HELP = '''Select the kind of record you want to attach
    a footnote to, and then use the object id search button to select an item.'''
    fieldsets = [
        (None, {
            'fields':('content_type', 'object_id'),
            'description': '<div class="help">%s</div>' % CONTENT_LOOKUP_HELP
        }),
        (None, {
            'fields': ('bibliography', 'location', 'snippet_text', 'is_agree',
                'notes')
        })
    ]

    related_lookup_fields = {
        'generic': [['content_type', 'object_id']]
    }


class FootnoteInline(GenericTabularInline):
    model = Footnote
    classes = ('grp-collapse grp-closed', )  # grapelli collapsible
    fields = ('bibliography', 'location', 'snippet_text', 'is_agree', 'notes')
    extra = 1


class SourceTypeAdmin(NamedNotableAdmin):
    list_display = NamedNotableAdmin.list_display + ('item_count', )


class BibliographyAdmin(admin.ModelAdmin):
    list_display = ('bibliographic_note', 'source_type', 'footnote_count',
        'note_snippet')
    search_fields = ('bibliographic_note', 'notes')
    fields = ('source_type', 'bibliographic_note', 'notes')
    list_filter = ('source_type',)


admin.site.register(SourceType, SourceTypeAdmin)
admin.site.register(Bibliography, BibliographyAdmin)
admin.site.register(Footnote, FootnoteAdmin)
