import bleach
from django.db import models
from django.template.defaultfilters import striptags, truncatechars_html
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.blocks import (RichTextBlock, StreamBlock, StructBlock,
                                 TextBlock)
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.edit_handlers import ImageChooserPanel

from mep.common.utils import absolutize_url
from mep.common.views import RdfViewMixin


class CaptionedImageBlock(StructBlock):
    ''':class:`~wagtail.core.blocks.StructBlock` for an image with
    alternative text and optional formatted caption, so
    that both caption and alternative text can be context-specific.'''
    image = ImageChooserBlock()
    alternative_text = TextBlock(
        required=True,
        help_text='Alternative text for visually impaired users to ' +
                  'briefly communicate the intended message of the '
                  'image in this context.')
    caption = RichTextBlock(features=['bold', 'italic', 'link'],
                                   required=False)

    class Meta:
        icon = 'image'


class BodyContentBlock(StreamBlock):
    '''Common set of content blocks for content/analysis pages.'''
    paragraph = RichTextBlock(features=['h3', 'h4', 'bold', 'italic', 'link',
                                        'ol', 'ul', 'blockquote'])
    image = ImageChooserBlock()
    captioned_image = CaptionedImageBlock()
    document = DocumentChooserBlock()
    footnotes = RichTextBlock(
        features=['ol', 'ul', 'bold', 'italic', 'link'],
        classname='footnotes'
    )


class HomePage(Page):
    ''':class:`wagtail.core.models.Page` model for S&Co. home page.'''
    parent_page_types = [Page]  # can only be child of Root
    body = StreamField(BodyContentBlock)
    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        verbose_name = 'homepage'


class RdfPageMixin(RdfViewMixin):
    '''Adapt :class:`mep.common.view.RdfViewMixin` for Wagtail pages'''

    def get_absolute_url(self):
        return self.url

    def get_breadcrumbs(self):
        '''Get the list of breadcrumbs and links to display for this page.'''
        crumbs = [
            ('Home', absolutize_url('/'))
        ]
        # if parent is not the home page, include in breadcrumbs
        parent = self.get_parent()
        if not hasattr(parent, 'homepage'):
            crumbs.append((parent.seo_title or parent.title, parent.url))
        # add current page to breadcrumbs
        crumbs.append((self.seo_title or self.title, self.url))
        return crumbs


class LandingPage(RdfPageMixin, Page):
    ''':class:`wagtail.core.models.Page` model for aggregating other pages.'''
    parent_page_types = [HomePage]  # can only be child of HomePage
    tagline = models.CharField(max_length=500)  # shown just below the header
    body = StreamField(BodyContentBlock, blank=True)
    header_image = models.ForeignKey(  # image that will be used for the header
        'wagtailimages.image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'  # no reverse relationship
    )
    content_panels = Page.content_panels + [
        ImageChooserPanel('header_image'),
        FieldPanel('tagline'),
        StreamFieldPanel('body')
    ]


class PagePreviewDescriptionMixin(models.Model):
    '''Page mixin with logic for page preview content. Adds an optional
    richtext description field, and methods to get description and plain-text
    description, for use in previews on the site and plain-text metadata
    previews.'''

    # adapted from PPA; does not allow <p> tags in description

    description = RichTextField(
        blank=True, features=['bold', 'italic'],
        help_text='Optional. Brief description for preview display. Will ' +
        'also be used for search description (without tags), if one is ' +
        'not entered.')

    #: maximum length for description to be displayed
    max_length = 225

    # ('a' is omitted by subsetting default ALLOWED_TAGS)
    #: allowed tags for bleach html stripping in description
    allowed_tags = list((set(bleach.sanitizer.ALLOWED_TAGS) - set(['a'])))

    class Meta:
        abstract = True

    def get_description(self):
        '''Get formatted description for preview. Uses description field
        if there is content, otherwise uses beginning of the body content.'''

        description = ''

        # use description field if set
        # use striptags to check for empty paragraph)
        if striptags(self.description):
            description = self.description

        # if not, use beginning of body content
        else:
            # Iterate over blocks and use content from first paragraph content
            for block in self.body:
                if block.block_type == 'paragraph':
                    description = block
                    # stop after the first instead of using last
                    break

        description = bleach.clean(
            str(description),
            tags=self.allowed_tags,
            strip=True
        )
        # truncate either way
        return truncatechars_html(description, self.max_length)

    def get_plaintext_description(self):
        '''Get plain-text description for use in metadata. Uses
        search_description field if set; otherwise uses the result of
        :meth:`get_description` with tags stripped.'''

        if self.search_description.strip():
            return self.search_description
        return striptags(self.get_description())


class ContentPage(RdfPageMixin, Page, PagePreviewDescriptionMixin):
    '''Basic :class:`wagtail.core.models.Page` model.'''
    parent_page_types = [LandingPage]  # can only be child of LandingPage
    body = StreamField(BodyContentBlock)
    #: featured image for tile preview and social media
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Preview image for landing page list (if supported)' +
                  ' and social media.'
    )
    content_panels = Page.content_panels + [
        FieldPanel('description'),
        ImageChooserPanel('featured_image'),
        StreamFieldPanel('body'),
    ]
