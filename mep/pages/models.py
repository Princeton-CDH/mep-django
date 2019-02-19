from django.db.models import SET_NULL, CharField, ForeignKey
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.blocks import RichTextBlock, StreamBlock, StructBlock
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.edit_handlers import ImageChooserPanel


class CaptionedImageBlock(StructBlock):
    ''':class:`~wagtail.core.blocks.StructBlock` for an image with
    a formatted caption, so caption can be context-specific.'''
    image = ImageChooserBlock()
    caption = RichTextBlock(features=['bold', 'italic', 'link'])

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
    parent_page_types = [Page] # can only be child of Root
    body = StreamField(BodyContentBlock)
    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        verbose_name = 'homepage'


class LandingPage(Page):
    ''':class:`wagtail.core.models.Page` model for aggregating other pages.'''
    parent_page_types = [HomePage] # can only be child of HomePage
    tagline = CharField(max_length=500) # shown just below the header
    body = StreamField(BodyContentBlock)
    header_image = ForeignKey( # image that will be used for the header
        'wagtailimages.image',
        null=True,
        blank=True,
        on_delete=SET_NULL,
        related_name='+' # no reverse relationship
    )
    content_panels = Page.content_panels + [
        ImageChooserPanel('header_image'),
        FieldPanel('tagline'),
        StreamFieldPanel('body')
    ]


class ContentPage(Page):
    '''Basic :class:`wagtail.core.models.Page` model.'''
    parent_page_types = [LandingPage] # can only be child of LandingPage
    body = StreamField(BodyContentBlock)
    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]
