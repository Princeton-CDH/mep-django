from datetime import date

import bleach
from django.db import models
from django.http import Http404
from django.template.defaultfilters import striptags, truncatechars_html
from django.utils.functional import cached_property
from django.utils.text import slugify
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.models import Image
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet

from mep.common.utils import absolutize_url
from mep.common.views import RdfViewMixin

#: help text for image alternative text
ALT_TEXT_HELP = """Alternative text for visually impaired users to
briefly communicate the intended message of the image in this context."""


class CaptionedImageBlock(blocks.StructBlock):
    ''':class:`~wagtail.core.blocks.StructBlock` for an image with
    alternative text and optional formatted caption, so
    that both caption and alternative text can be context-specific.'''
    image = ImageChooserBlock()
    alternative_text = blocks.TextBlock(required=True, help_text=ALT_TEXT_HELP)
    caption = blocks.RichTextBlock(features=['bold', 'italic', 'link'],
                                   required=False)

    class Meta:
        icon = 'image'
        template = 'pages/blocks/captioned_image_block.html'


class SVGImageBlock(blocks.StructBlock):
    ''':class:`~wagtail.core.blocks.StructBlock` for an SVG image with
    alternative text and optional formatted caption. Separate from
    :class:`CaptionedImageBlock` because Wagtail image handling
    does not work with SVG.'''
    extended_description_help = '''This text will only be read to \
    non-sighted users and should describe the major insights or \
    takeaways from the graphic. Multiple paragraphs are allowed.'''

    image = DocumentChooserBlock()
    alternative_text = blocks.TextBlock(required=True, help_text=ALT_TEXT_HELP)
    caption = blocks.RichTextBlock(features=['bold', 'italic', 'link'],
                                   required=False)
    extended_description = blocks.RichTextBlock(
        features=['p'], required=False, help_text=extended_description_help)

    class Meta:
        icon = 'image'
        label = 'SVG'
        template = 'pages/blocks/svg_image_block.html'


class LinkableSectionBlock(blocks.StructBlock):
    ''':class:`~wagtail.core.blocks.StructBlock` for a rich text block and an
    associated `title` that will render as an <h2>. Creates an anchor (<a>)
    so that the section can be directly linked to using a url fragment.'''
    title = blocks.CharBlock()
    anchor_text = blocks.CharBlock(help_text='Short label for anchor link')
    body = blocks.RichTextBlock()
    panels = [
        FieldPanel('title'),
        FieldPanel('slug'),
        FieldPanel('body'),
    ]

    class Meta:
        icon = 'form'
        label = 'Linkable Section'
        template = 'pages/snippets/linkable_section.html'

    def clean(self, value):
        cleaned_values = super().clean(value)
        # run slugify to ensure anchor text is a slug
        cleaned_values['anchor_text'] = slugify(cleaned_values['anchor_text'])
        return cleaned_values


class BodyContentBlock(blocks.StreamBlock):
    '''Common set of content blocks for content/analysis pages.'''
    paragraph = blocks.RichTextBlock(
        features=['h3', 'h4', 'bold', 'italic', 'link',
                  'ol', 'ul', 'blockquote'])
    image = CaptionedImageBlock()
    svg_image = SVGImageBlock()
    document = DocumentChooserBlock()
    footnotes = blocks.RichTextBlock(
        features=['ol', 'ul', 'bold', 'italic', 'link'],
        classname='footnotes'
    )
    linkable_section = LinkableSectionBlock()


class HomePage(Page):
    ''':class:`wagtail.core.models.Page` model for S&Co. home page.'''
    # can only be child of Root
    parent_page_types = [Page]
    # only landingpage subtypes as children
    subpage_types = ['ContentLandingPage', 'EssayLandingPage']
    #: main page text
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
            crumbs.append((parent.seo_title or parent.title,
                           absolutize_url(parent.url)))
        # add current page to breadcrumbs
        crumbs.append((self.seo_title or self.title, absolutize_url(self.url)))
        return crumbs


class LandingPage(RdfPageMixin, Page):
    '''Abstract :class:`wagtail.core.models.Page` model for aggregating other
    pages as its children.'''

    # must be a child of the HomePage directly
    parent_page_types = ['HomePage']
    #: short introductory text shown just below the header, before content
    tagline = models.CharField(max_length=500)
    #: main page text
    body = StreamField(BodyContentBlock, blank=True)
    #: image that will be used for the header
    header_image = models.ForeignKey(
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

    class Meta:
        abstract = True


class ContentLandingPage(LandingPage):
    ''':class:`LandingPage` subclass that aggregates :class:`ContentPage`s as
    its children.'''

    # children must be ContentPages
    subpage_types = ['ContentPage']


class EssayLandingPage(LandingPage):
    ''':class:`LandingPage` subclass that aggregates :class:`EssayPage`s as
    its children by publication date, using a 'date + slug' routing scheme.'''

    #: children must be EssayPages
    subpage_types = ['EssayPage']
    # template
    # template = 'pages/essay_landing_page.html'

    def get_context(self, request):
        '''Add child Essays sorted by publication date to the context'''
        context = super().get_context(request)

        # Add extra variables and return the updated context
        context['essays'] = EssayPage.objects.child_of(self).live() \
                                     .order_by('-first_published_at')
        return context

    def route(self, request, path_components):
        '''Customize child content page routing to serve content pages
        by year/month/slug.'''

        # NOTE: might be able to use RoutablePageMixin for this,
        # but could not get that to work. Current version adapted from PPA.

        if path_components:

            # if not enough path components are specified, raise a 404
            if len(path_components) < 3:
                raise Http404
                # (could eventually handle year/month to display essays by
                # date, but not yet implemented)

            # currently only handle year/month/post-slug/
            if len(path_components) >= 3:
                # request is for a child of this page

                # not using a regex route, so check character count
                # - want a four-digit year and a two-digit month
                if len(path_components[0]) != 4 or len(path_components[1]) != 2:
                    raise Http404

                try:
                    year = int(path_components[0])
                    month = int(path_components[1])
                except ValueError:
                    # if year or month are not numeric, then 404
                    raise Http404

                child_slug = path_components[2]
                remaining_components = path_components[3:]

                # find a matching child or 404
                try:
                    subpage = self.get_children().get(
                        first_published_at__year=year,
                        first_published_at__month=month,
                        slug=child_slug)
                except Page.DoesNotExist:
                    raise Http404

                # delegate further routing to child page
                return subpage.specific.route(request, remaining_components)

        else:
            # handle normally (display current page)
            return super().route(request, path_components)


class PagePreviewDescriptionMixin(models.Model):
    '''Page mixin with logic for page preview content. Adds an optional
    richtext description field, and methods to get description and plain-text
    description, for use in previews on the site and plain-text metadata
    previews.'''

    # adapted from PPA; does not allow <p> tags in description
    #: brief description for preview display
    description = RichTextField(
        blank=True, features=['bold', 'italic'],
        help_text='Optional. Brief description for preview display. Will ' +
        'also be used for search description (without tags), if one is ' +
        'not entered.')
    #: maximum length for description to be displayed
    max_length = 225
    # (tags are omitted by subsetting default ALLOWED_TAGS)
    #: allowed tags for bleach html stripping in description
    allowed_tags = list((set(bleach.sanitizer.ALLOWED_TAGS) - \
        set(['a', 'blockquote']))) # additional tags to remove

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


@register_snippet
class Person(models.Model):
    '''Common model for a person, currently used to document authorship for
    instances of :class:`BasePage`. Adapted from PPA.'''

    #: first or given name and all non-family names (i.e. middle names)
    # NOTE this is everything *before* the comma in a citation
    first_name = models.CharField(
        max_length=255,
        help_text='First or given name and all non-family or middle names, e.g.'
                   '"Henry Wadsworth", as it would appear in a citation.'
    )
    #: last or family name of an individual
    last_name = models.CharField(
        max_length=255,
        help_text='Last or family name, e.g. "Longfellow".'
    )
    #: identifying URI for a person (VIAF, ORCID iD, personal website, etc.)
    url = models.URLField(
        blank=True,
        default='',
        help_text='Personal website, profile page, or social media profile page'
                  'for this person.'
    )
    #: twitter creator ID - used for twitter card previews
    # NOTE this is not a username! you can find your creator ID using a tool:
    # http://gettwitterid.com or https://tweeterid.com/
    # it will never change, unlike a username.
    # this ID form can be used for more preview types than a simple username; see
    # http://developer.twitter.com/en/docs/tweets/optimize-with-cards/overview/markup
    twitter_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Twitter user ID. Note that this is NOT a username - you can'
                  'find yours at http://tweeterid.com/. Will not change if a'
                  'username changes.'
    )

    panels = [
        FieldPanel('name'),
        FieldPanel('url'),
        FieldPanel('twitter_id'),
    ]

    def __str__(self):
        return self.name

    @property
    def name(self):
        '''Return the Person's name in "Firstname Lastname" format.'''
        return '%s %s' % (self.first_name, self.last_name)

    @property
    def lastname_first(self):
        '''Return the Person's name in "Lastname, Firstname" format.'''
        return '%s, %s' % (self.last_name, self.first_name)


class BasePage(RdfPageMixin, Page, PagePreviewDescriptionMixin):
    '''Abstract :class:`wagtail.core.models.Page` model that contains all
    functionality to be shared across `Page` subtypes.'''

    #: main page text
    body = StreamField(BodyContentBlock)
    #: authors - collection of Person snippets
    authors = StreamField(
        [('author', SnippetChooserBlock(Person))],
        blank=True,
        help_text='Select or create new people to add as authors.'
    )
    #: editors - collection of Person snippets
    editors = StreamField(
        [('editor', SnippetChooserBlock(Person))],
        blank=True,
        help_text='Select or create new people to add as editors.'
    )
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
        StreamFieldPanel('authors'),
        StreamFieldPanel('editors'),
        ImageChooserPanel('featured_image'),
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class ContentPage(BasePage):
    '''A simple :class:`BasePage` type that appears beneath `ContentLandingPage`s
    in the hierarchy.'''

    # can only be child of ContentLandingPage
    parent_page_types = ['ContentLandingPage']
    # no allowed children
    subpage_types = []


class EssayPage(BasePage):
    '''A :class:`BasePage` type that appears beneath `EssayLandingPage`s
    in the hierarchy.'''

    # can only be child of EssayLandingPage
    parent_page_types = ['EssayLandingPage']
    # no allowed children
    subpage_types = []


    # taken from PPA
    def set_url_path(self, parent):
        """
        Generate the url_path field based on this page's slug, first publication date,
        and the specified parent page. Adapted from default logic to include
        publication date.
        (Parent is passed in for previewing unsaved pages)
        """
        # use current date for preview if first published is not set
        post_date = self.first_published_at or date.today()
        if parent:
            self.url_path = '{}{}/{}/'.format(
                parent.url_path, post_date.strftime('%Y/%m'), self.slug)
        else:
            # a page without a parent is the tree root, which always has a url_path of '/'
            self.url_path = '/'

        return self.url_path
