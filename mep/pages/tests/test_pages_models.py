from unittest.mock import Mock

from django.template.defaultfilters import striptags
from django.test import SimpleTestCase, TestCase
from wagtail.models import Page, Site
from wagtail.documents.models import Document
from wagtail.test.utils import WagtailPageTests
from wagtail.test.utils.form_data import nested_form_data, rich_text, streamfield
from mep.pages.models import (
    CaptionedImageBlock,
    ContentLandingPage,
    ContentPage,
    EssayLandingPage,
    EssayPage,
    HomePage,
    LinkableSectionBlock,
    SVGImageBlock,
    Person,
)
import wagtail_factories
from wagtail import blocks
import factory
from wagtail.rich_text import RichText


class TestLinkableSectionBlock(SimpleTestCase):
    def test_clean(self):
        block = LinkableSectionBlock()
        cleaned_values = block.clean({"anchor_text": "lending library plans"})
        assert cleaned_values["anchor_text"] == "lending-library-plans"

    def test_render(self):
        block = LinkableSectionBlock()
        html = block.render(
            block.to_python(
                {
                    "title": "Joining the Lending Library",
                    "body": "Info about lending library subscription plans",
                    "anchor_text": "joining-the-lending-library",
                }
            )
        )
        expected_html = """
            <div id="joining-the-lending-library">
            <h2>Joining the Lending Library
            <a class="headerlink" href="#joining-the-lending-library"
               title="Permalink to this section">¶</a>
            </h2>
            <div class="rich-text">
                Info about lending library subscription plans
            </div>
            </div>
        """

        self.assertHTMLEqual(html, expected_html)


class TestCaptionedImageBlock(SimpleTestCase):
    def test_render(self):
        block = CaptionedImageBlock()
        test_img = {"url": "kitty.png", "width": 100, "height": 200}
        alt_text = "picture of a kitten"
        # NOTE: using "img" here instead of "image" means we're
        # not actually testing the image logic; but not clear how
        # to mock or use an image object in a test
        html = block.render(
            block.to_python({"img": test_img, "alternative_text": alt_text})
        )
        assert "<figure>" in html
        assert '<img srcset="' in html
        assert 'alt="picture of a kitten" ' in html
        # no caption
        assert "<figcaption>" not in html

        # with caption
        caption = "A kitten curled up in the sunshine"
        html = block.render(
            block.to_python(
                {"img": test_img, "alternative_text": alt_text, "caption": caption}
            )
        )
        assert (
            '<figcaption><div class="rich-text">%s</div></figcaption' % caption
        ) in html


class TestSVGImageBlock(SimpleTestCase):
    def test_render(self):
        block = SVGImageBlock()
        test_svg = {"url": "graph.svg"}  # Mock(spec=Document, url='graph.svg')
        alt_text = "membership timeline"
        html = block.render({"image": test_svg, "alternative_text": alt_text})
        assert ("<figure ") in html
        assert '<img role="img" ' in html
        # no caption, no extended description
        assert "<figcaption>" not in html
        assert '<div class="sr-only" ' not in html

        # with caption & extended description
        caption = "membership activity from 1919 to 1942"
        desc = "chart shows activity in 1920 and 1940"
        html = block.render(
            {
                "image": test_svg,
                "alternative_text": alt_text,
                "caption": caption,
                "extended_description": desc,
            }
        )
        assert ("<figcaption>%s</figcaption" % caption) in html
        assert '<div class="sr-only" id="graphsvg-desc">' in html
        assert desc in html


##########################
# PAGE FACTORY for tests #
##########################

class PageFactory(wagtail_factories.PageFactory):
    title=""
    slug=""
    body=wagtail_factories.StreamFieldFactory({
        "paragraph":factory.SubFactory(wagtail_factories.CharBlockFactory),
        "footnotes":factory.SubFactory(wagtail_factories.CharBlockFactory)
    })

    class Meta:
        model = Page

class PageTester(WagtailPageTests):
    def setUp(self):
        self.site = Site.objects.first()
        self.homepage = HomePageFactory.create(
            body__0__paragraph=RichText(HOMEPAGE_PARA),
            body__1__footnotes=RichText(HOMEPAGE_FOOT),
        )
        self.site.root_page = self.homepage
        self.site.save()
        self.site.refresh_from_db()

def assert_page_body_contains(page, paragraph, footnote=""):
    body = page.body

    if paragraph and footnote:
        assert len(body) == 2
        block1,block2 = body
        type1,type2=block1.block_type, block2.block_type
        val1,val2=block1.value.source, block2.value.source
        
        assert type2 == 'footnotes'
        assert val2 == footnote
    else:
        assert len(body) == 1
        block1, = body
        type1=block1.block_type
        val1=block1.value.source

    assert type1 == 'paragraph'
    assert val1 == paragraph
        


###################
# HOME PAGE tests #
################### 

HOMEPAGE_TITLE = "S&Co."
HOMEPAGE_SLUG= "newhome"
HOMEPAGE_PARA="homepage body text"
HOMEPAGE_FOOT="homepage footnotes"

class HomePageFactory(PageFactory):
    title=HOMEPAGE_TITLE
    slug=HOMEPAGE_SLUG
    class Meta:
        model = HomePage

class TestHomePage(PageTester):
    def test_can_create(self):
        self.assertIsNotNone(self.homepage.pk)
        assert self.homepage.title == HOMEPAGE_TITLE
        assert self.homepage.slug == HOMEPAGE_SLUG
        assert_page_body_contains(
            self.homepage,
            HOMEPAGE_PARA,
            HOMEPAGE_FOOT
        )

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(HomePage, [Page])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(
            HomePage, [ContentLandingPage, EssayLandingPage, ContentPage]
        )

    def test_template(self):
        url = self.homepage.relative_url(self.site)
        response = self.client.get(url)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "pages/home_page.html")




######################
# LANDING PAGE tests #
######################

LANDINGPAGE_TITLE="My Kinda Landing Page!"
LANDINGPAGE_SLUG="mylp"
LANDINGPAGE_TAGLINE="now thats what im talkin about"
LANDINGPAGE_PARA="this landing page rules"
LANDINGPAGE_FOOT="footnotes to prove it, baby"

class LandingPageFactory(PageFactory):
    title=LANDINGPAGE_TITLE
    slug=LANDINGPAGE_SLUG
    tagline=LANDINGPAGE_TAGLINE
    class Meta:
        model = ContentLandingPage

class TestLandingPage(PageTester):
    def setUp(self):
        super().setUp()
        self.page = LandingPageFactory.create(
            body__0__paragraph=RichText(LANDINGPAGE_PARA),
            body__1__footnotes=RichText(LANDINGPAGE_FOOT),
        )

    def test_can_create(self):
        self.assertIsNotNone(self.page.pk)
        assert self.page.title == LANDINGPAGE_TITLE
        assert self.page.slug == LANDINGPAGE_SLUG
        assert self.page.tagline == LANDINGPAGE_TAGLINE
        assert_page_body_contains(
            self.page,
            LANDINGPAGE_PARA,
            LANDINGPAGE_FOOT
        )

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(ContentLandingPage, [HomePage])



##############################
# CONTENT LANDING PAGE tests #
##############################

CONTENTLANDINGPAGE_TITLE="Sources 2"
CONTENTLANDINGPAGE_SLUG="sources2"
CONTENTLANDINGPAGE_TAGLINE="like sources, but better"
CONTENTLANDINGPAGE_PARA="the new sources landing page"
CONTENTLANDINGPAGE_FOOT="some landing page footnotes"

class ContentLandingPageFactory(PageFactory):
    title=CONTENTLANDINGPAGE_TITLE
    slug=CONTENTLANDINGPAGE_SLUG
    tagline=CONTENTLANDINGPAGE_TAGLINE
    class Meta:
        model = ContentLandingPage

class TestContentLandingPage(PageTester):
    def setUp(self):
        super().setUp()
        self.page = ContentLandingPageFactory.create(
            body__0__paragraph=RichText(CONTENTLANDINGPAGE_PARA),
            body__1__footnotes=RichText(CONTENTLANDINGPAGE_FOOT),
            parent=self.homepage
        )

    def test_can_create(self):
        self.assertIsNotNone(self.page.pk)
        assert self.page.title == CONTENTLANDINGPAGE_TITLE
        assert self.page.slug == CONTENTLANDINGPAGE_SLUG
        assert self.page.tagline == CONTENTLANDINGPAGE_TAGLINE
        assert_page_body_contains(
            self.page,
            CONTENTLANDINGPAGE_PARA,
            CONTENTLANDINGPAGE_FOOT
        )

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(ContentLandingPage, [HomePage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(ContentLandingPage, [ContentPage])

    def test_template(self):
        url = self.page.relative_url(self.site)
        response = self.client.get(url)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "pages/landing_page.html")
        self.assertTemplateUsed(response, "pages/content_landing_page.html")



############################
# ESSAY LANDING PAGE tests #
############################

ESSAYLANDINGPAGE_TITLE="Analysis 2"
ESSAYLANDINGPAGE_SLUG="analysis2"
ESSAYLANDINGPAGE_TAGLINE="do some more analysis"
ESSAYLANDINGPAGE_PARA="the second analysis landing page"

ESSAYPAGE_TITLE="Test Analysis"
ESSAYPAGE_SLUG="test-analysis"

class EssayLandingPageFactory(PageFactory):
    title=ESSAYLANDINGPAGE_TITLE
    slug=ESSAYLANDINGPAGE_SLUG
    tagline=ESSAYLANDINGPAGE_TAGLINE
    class Meta:
        model = EssayLandingPage

class EssayPageFactory(PageFactory):
    title=ESSAYPAGE_TITLE
    slug=ESSAYPAGE_SLUG
    class Meta:
        model = EssayPage


class TestEssayLandingPage(PageTester):
    def setUp(self):
        super().setUp()
        self.page = EssayLandingPageFactory.create(
            body__0__paragraph=RichText(ESSAYLANDINGPAGE_PARA),
            parent=self.homepage
        )
        self.essay = EssayPageFactory.create(parent=self.page)

    def test_can_create(self):
        self.assertIsNotNone(self.page.pk)
        assert self.page.title == ESSAYLANDINGPAGE_TITLE
        assert self.page.slug == ESSAYLANDINGPAGE_SLUG
        assert self.page.tagline == ESSAYLANDINGPAGE_TAGLINE
        assert_page_body_contains(
            self.page,
            ESSAYLANDINGPAGE_PARA,
        )

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(EssayLandingPage, [HomePage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(EssayLandingPage, [EssayPage])

    def test_template(self):
        url = self.page.relative_url(self.site)
        response = self.client.get(url)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "pages/landing_page.html")
        self.assertTemplateUsed(response, "pages/essay_landing_page.html")

    def test_get_context(self):
        analysis_index = self.page
        analysis_essay = self.essay
        context = analysis_index.get_context({})
        assert "essays" in context
        assert analysis_essay in context["essays"]

        # set to not published
        analysis_essay.live = False
        analysis_essay.save()
        context = analysis_index.get_context({})
        assert analysis_essay not in context["essays"]

        # TODO create some newer essays to test ordering by pub date




###################
# BASE PAGE tests #
###################


class TestBasePage(WagtailPageTests):
    def test_get_description(self):
        """test page preview mixin"""
        # page with body content and no description
        mypage = ContentPage(
            title="Undescribable", body=(("paragraph", "<p>How to <a>begin</a>?</p>"),)
        )

        assert not mypage.description
        desc = mypage.get_description()
        # length excluding tags should be truncated to max length or less
        assert len(striptags(desc)) <= mypage.max_length
        # beginning of text should match exactly the *first* block
        # (excluding end of content because truncation is inside tags)

        # should also be cleaned by bleach to its limited set of tags
        assert desc[:200] == "How to begin?"

        # empty tag should be stripped
        mypage.body = [("paragraph", "<p></p>")]
        desc = mypage.get_description()
        assert desc == ""

        # blockquotes should be stripped
        mypage.body = [("paragraph", "<p><blockquote>h</blockquote>i</p>")]
        desc = mypage.get_description()
        assert desc == "\nhi"

        # test content page with image for first block
        mypage2 = ContentPage(
            title="What is Prosody?",
            body=[
                ("image", '<img src="milton-example.png"/>'),
                (
                    "paragraph",
                    "<p>Prosody today means both the study of "
                    'and <a href="#">pronunciation</a></p>',
                ),
                ("paragraph", "<p>More content here...</p>"),
            ],
        )
        # should ignore image block and use first paragraph content
        assert (
            mypage2.get_description()[:200]
            == "Prosody today means both the study of and pronunciation"
        )

        # should remove <a> tags
        assert '<a href="#">' not in mypage2.get_description()

        # should use description field when set
        intro_text = "A short intro to prosody."
        mypage2.description = "<p>%s</p>" % intro_text
        assert mypage2.get_description() == intro_text

        # should truncate if description content is too long
        mypage2.description = mypage.body[0]
        assert len(striptags(mypage.get_description())) <= mypage.max_length



######################
# CONTENT PAGE tests #
######################

CONTENTPAGE_TITLE="More about information"
CONTENTPAGE_SLUG="new-about"
CONTENTPAGE_PARA="this page lives right under about"


class ContentPageFactory(PageFactory):
    title=CONTENTPAGE_TITLE
    slug=CONTENTPAGE_SLUG
    class Meta:
        model = ContentPage



class TestContentPage(PageTester):
    def setUp(self):
        super().setUp()
        self.landingpage = ContentLandingPageFactory.create(
            body__0__paragraph=RichText(CONTENTLANDINGPAGE_PARA),
            body__1__footnotes=RichText(CONTENTLANDINGPAGE_FOOT),
            parent=self.homepage
        )
        self.page = ContentPageFactory.create(
            body__0__paragraph=RichText(CONTENTPAGE_PARA),
            parent=self.landingpage,
        )

    def test_can_create(self):
        self.assertIsNotNone(self.page.pk)
        assert self.page.title == CONTENTPAGE_TITLE
        assert self.page.slug == CONTENTPAGE_SLUG
        assert_page_body_contains(
            self.page,
            CONTENTPAGE_PARA,
        )

    def test_template(self):
        url = self.page.relative_url(self.site)
        response = self.client.get(url)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "pages/base_page.html")
        self.assertTemplateUsed(response, "pages/content_page.html")

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(ContentPage, [ContentLandingPage, HomePage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(ContentPage, [])




####################
# ESSAY PAGE tests #
####################

SECONDESSAYPAGE_TITLE="A new analysis esssay"
SECONDESSAYPAGE_SLUG="new-essay"
SECONDESSAYPAGE_PARA="this page lives right under analysis"

class TestEssayPage(PageTester):
    def setUp(self):
        super().setUp()
        self.landingpage = EssayLandingPageFactory.create(
            body__0__paragraph=RichText(ESSAYLANDINGPAGE_PARA),
            parent=self.homepage
        )
        self.page = EssayPageFactory.create(
            title=SECONDESSAYPAGE_TITLE,
            slug=SECONDESSAYPAGE_SLUG,
            body__0__paragraph=RichText(SECONDESSAYPAGE_PARA),
            parent=self.landingpage
        )

    def test_can_create(self):
        self.assertIsNotNone(self.page.pk)
        assert self.page.title == SECONDESSAYPAGE_TITLE
        assert self.page.slug == SECONDESSAYPAGE_SLUG
        assert_page_body_contains(
            self.page,
            SECONDESSAYPAGE_PARA,
        )

    def test_template(self):
        url = self.page.relative_url(self.site)
        print('getting url:', url)
        response = self.client.get(url)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "pages/base_page.html")
        self.assertTemplateUsed(response, "pages/essay_page.html")

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(EssayPage, [EssayLandingPage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(EssayPage, [])

    def test_set_url_path(self):
        # TODO
        pass


class TestPerson(TestCase):
    def test_name(self):
        # first and last name
        person = Person.objects.create(first_name="James", last_name="Joyce")
        assert person.name == "James Joyce"
        # middle names
        person = Person.objects.create(
            first_name="Henry Wadsworth", last_name="Longfellow"
        )
        assert person.name == "Henry Wadsworth Longfellow"

    def test_lastname_first(self):
        # first and last name
        person = Person.objects.create(first_name="James", last_name="Joyce")
        assert person.lastname_first == "Joyce, James"
        # middle names
        person = Person.objects.create(
            first_name="Henry Wadsworth", last_name="Longfellow"
        )
        assert person.lastname_first == "Longfellow, Henry Wadsworth"
