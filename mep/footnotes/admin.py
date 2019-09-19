from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from dal import autocomplete

from mep.common.admin import NamedNotableAdmin
from mep.footnotes.models import Bibliography, Footnote, SourceType


class FootnoteAdminForm(forms.ModelForm):
    class Meta:
        model = Footnote
        fields = ('__all__')
        widgets = {
            'bibliography': autocomplete.ModelSelect2(
                url='footnotes:bibliography-autocomplete',
                attrs={
                    'data-placeholder': 'Type to search for bibliography... ',
                    'data-minimum-input-length': 3
                }
            ),
        }


def figgy_uri_from_manifest(manifest_uri):
    '''Generate a figgy item url from manifest or canvas id.'''
    # this logic is figgy-specific
    return manifest_uri.replace('/concern/scanned_resources/',
                                '/catalog/') \
                       .partition('/manifest')[0]


class FootnoteAdmin(admin.ModelAdmin):
    form = FootnoteAdminForm
    list_display = ('content_object', 'bibliography', 'location',
                    'image', 'is_agree')
    list_filter = ('bibliography__source_type', 'content_type')
    search_fields = ('bibliography__bibliographic_note', 'location', 'notes')
    CONTENT_LOOKUP_HELP = '''Select the kind of record you want to attach
    a footnote to, and then use the object id search button to select an item.'''
    fieldsets = [
        (None, {
            'fields': ('content_type', 'object_id'),
            'description': '<div class="help">%s</div>' % CONTENT_LOOKUP_HELP
        }),
        (None, {
            'fields': (
                'bibliography', 'location',
                ('image', 'image_thumbnail'),
                'snippet_text', 'is_agree', 'notes')
        })
    ]

    readonly_fields = ('image_thumbnail',)

    related_lookup_fields = {
        'generic': [['content_type', 'object_id']]
    }

    def image_thumbnail(self, obj):
        '''thumbnail for image location if associated'''
        if obj.image:
            img = obj.image.admin_thumbnail()
            if 'figgy.princeton' in obj.image.uri:
                img = '<a target="_blank" href="%s">%s</a>' % \
                    (figgy_uri_from_manifest(obj.image.uri),
                     img)
            return img
    image_thumbnail.allow_tags = True


class FootnoteInline(GenericTabularInline):
    model = Footnote
    form = FootnoteAdminForm
    classes = ('grp-collapse grp-closed', )  # grapelli collapsible
    fields = ('bibliography', 'location', 'snippet_text', 'is_agree', 'notes')
    extra = 1


class SourceTypeAdmin(NamedNotableAdmin):
    list_display = NamedNotableAdmin.list_display + ('item_count', )


class BibliographyAdmin(admin.ModelAdmin):
    list_display = (
        'bibliographic_note', 'source_type',
        'footnote_count', 'note_snippet', 'manifest_thumbnail'
    )
    search_fields = ('bibliographic_note', 'notes')
    fields = (
        'source_type', 'bibliographic_note', 'notes',
        ('manifest', 'manifest_thumbnail')
    )
    readonly_fields = ('manifest_thumbnail', )
    list_filter = ('source_type',)

    def manifest_thumbnail(self, obj):
        if obj.manifest:
            img = obj.manifest.admin_thumbnail()
            if 'figgy.princeton' in obj.manifest.uri:
                img = '<a target="_blank" href="%s">%s</a>' % \
                    (figgy_uri_from_manifest(obj.manifest.uri),
                     img)
            return img
    manifest_thumbnail.allow_tags = True

# TODO: digital edition autocomplete?

admin.site.register(SourceType, SourceTypeAdmin)
admin.site.register(Bibliography, BibliographyAdmin)
admin.site.register(Footnote, FootnoteAdmin)
