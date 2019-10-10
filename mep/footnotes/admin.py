from dal import autocomplete
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from djiffy.models import Canvas

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # for inline only, for now
        if 'image' not in self.fields:
            return

        # if no bibliography with manifest is associated,
        # don't allow associating a canvas
        canvas_qs = Canvas.objects.none()
        # if there is one, restrict canvas objects to those
        # associated with the manifest for this bibliography record
        if self.instance and hasattr(self.instance, 'bibliography') and \
           self.instance.bibliography.manifest:
            canvas_qs = Canvas.objects.filter(
                manifest=self.instance.bibliography.manifest)

        self.fields['image'].queryset = canvas_qs


class FootnoteAdmin(admin.ModelAdmin):
    form = FootnoteAdminForm
    list_display = ('content_object', 'bibliography', 'location',
                    'image_thumbnail', 'is_agree')
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


class FootnoteInline(GenericTabularInline):
    model = Footnote
    form = FootnoteAdminForm
    classes = ('grp-collapse grp-closed', )  # grapelli collapsible
    fields = ('bibliography', 'location', 'image', 'image_thumbnail',
              'snippet_text', 'notes', 'is_agree')
    readonly_fields = ('image_thumbnail',)
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
        '''Use admin thumbnail from manifest if available, but wrap
        in a link using rendering url when present'''
        if obj.manifest:
            img = obj.manifest.admin_thumbnail()
            if 'rendering' in obj.manifest.extra_data:
                img = '<a target="_blank" href="%s">%s</a>' % \
                    (obj.manifest.extra_data['rendering']['@id'], img)
            return img
    manifest_thumbnail.allow_tags = True


# NOTE: it might be good to add canvas/manifest autocomplete in future


admin.site.register(SourceType, SourceTypeAdmin)
admin.site.register(Bibliography, BibliographyAdmin)
admin.site.register(Footnote, FootnoteAdmin)
