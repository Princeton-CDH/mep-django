from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from djiffy.models import Canvas, Manifest
from parasolr.indexing import Indexable

from mep.common.models import Named, Notable


class SourceType(Named, Notable):
    '''Type of source document.'''

    def item_count(self):
        '''number of associated bibliographic items'''
        return self.bibliography_set.count()
    item_count.short_description = '# items'


class Bibliography(Notable, Indexable):  # would citation be a better singular?
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

    @classmethod
    def index_item_type(cls):
        """Label for this kind of indexable item."""
        # override default behavior (using model verbose name)
        # since we are only care about indexing cards, and not
        # all bibliography records
        return 'card'

    @classmethod
    def items_to_index(cls):
        print('%s to index' % cls.objects.filter(account__isnull=False,
                                  manifest__isnull=False).count())

        return cls.objects.filter(account__isnull=False,
                                  manifest__isnull=False)

    def index_data(self):
        '''data for indexing in Solr'''
        index_data = super().index_data()
        # only library lending cards are indexed; if bibliography
        # does not have a manifest or is not associated with an account,
        # return id only.
        # This will blank out any previously indexed values, and item
        # will not be findable by any public searchable fields.
        account = self.account_set.all().first()
        if not self.manifest or not self.account_set.all().exists():
            del index_data['item_type']
            return index_data

        iiif_thumbnail = self.manifest.thumbnail.image

        # for now, store iiif thumbnail urls directly
        index_data['thumbnail_t'] = str(iiif_thumbnail.size(width=225))
        index_data['thumbnail2x_t'] = str(iiif_thumbnail.size(width=225 * 2))

        names = []
        account_years = set()
        for account in self.account_set.all():
            for person in account.persons.all():
                names.append(person.sort_name)
            account_years.update(set(date.year for date in
                                     account.event_dates))
        if names:
            index_data.update({
                'cardholder_t': names,
                'cardholder_sort_s': names[0],
            })

        if account_years:
            index_data.update({
                'years_is': list(account_years),
                'start_i': min(account_years),
                'end_i': max(account_years),
            })
        return index_data


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
