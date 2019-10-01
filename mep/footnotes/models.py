from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from djiffy.models import Canvas, Manifest

from mep.common.models import Named, Notable


class SourceType(Named, Notable):
    '''Type of source document.'''

    def item_count(self):
        '''number of associated bibliographic items'''
        return self.bibliography_set.count()
    item_count.short_description = '# items'


class Bibliography(Notable):  # would citation be a better singular?
    bibliographic_note = models.TextField(
        help_text='Full bibliographic citation')
    source_type = models.ForeignKey(SourceType)

    #: digital version as instance of :class:`djiffy.models.Manifest`
    manifest = models.ForeignKey(
        Manifest, blank=True, null=True, on_delete=models.SET_NULL,
        help_text='Digitized version of lending card, if locally available')

    class Meta:
        verbose_name_plural = 'Bibliographies'
        ordering = ('bibliographic_note',)

    def __str__(self):
        return self.bibliographic_note

    def footnote_count(self):
        '''number of footnotes this item is referenced in'''
        return self.footnote_set.count()
    footnote_count.short_description = '# footnotes'


class Footnote(Notable):
    '''Footnote that can be associated with any other model via
    generic relationship.  Used to provide supporting documentation
    for or against information in the system.
    '''
    bibliography = models.ForeignKey(Bibliography)
    location = models.TextField(
        blank=True,
        help_text='Page number for a book, URL for part of a website,' +
        ' or other location inside of a larger work.')
    snippet_text = models.TextField(blank=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        # restrict choices to "content" models (exclude django/admin models)
        # and models that are available in django admin
        # (otherwise, lookup is not possible)
        # TODO: add items here as the application expands
        limit_choices_to=models.Q(app_label='people',
            model__in=['country', 'person', 'address', 'profession']) |
            models.Q(
                app_label='accounts',
                model__in=['account', 'event', 'subscription', 'borrow',
                           'reimbursement', 'purchase']) |
            models.Q(app_label='books', model__in=['item'])
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    is_agree = models.BooleanField(
        'Supports', help_text='True if the evidence ' +
        'supports the information in the system, False if it contradicts.',
        default=True)

    image = models.ForeignKey(
        Canvas, blank=True, null=True,
        help_text='''Image location from an imported manifest, if available.''')

    def __str__(self):
        return 'Footnote on %s (%s)' % (self.content_object,
            ' '.join([str(i) for i in [self.bibliography, self.location] if i]))

    # NOTE: for convenient access from other models, add a
    # reverse generic relation
    #
    # from django.contrib.contenttypes.fields import GenericRelation
    # from mep.footnotes.models import Footnote
    #
    # footnotes = GenericRelation(Footnote)

    def image_thumbnail(self):
        '''Use admin thumbnail from image if available, but wrap
        in a link using rendering url from manifest when present'''
        if self.image:
            img = self.image.admin_thumbnail()
            if 'rendering' in self.image.manifest.extra_data:
                img = '<a target="_blank" href="%s">%s</a>' % \
                    (self.image.manifest.extra_data['rendering']['@id'], img)
            return img
    image_thumbnail.allow_tags = True
