from django.template.defaultfilters import striptags
from django.test import SimpleTestCase
from wagtail.core.models import Page, Site
from wagtail.tests.utils import WagtailPageTests
from wagtail.tests.utils.form_data import nested_form_data, rich_text, \
    streamfield

from mep.pages.models import ContentLandingPage, ContentPage, \
    EssayLandingPage, EssayPage, HomePage, LinkableSectionBlock


class TestLinkableSectionBlock(SimpleTestCase):

    def test_clean(self):
        block = LinkableSectionBlock()
        cleaned_values = block.clean({'anchor_text': 'lending library plans'})
        assert cleaned_values['anchor_text'] == 'lending-library-plans'

    def test_render(self):
        block = LinkableSectionBlock()
        html = block.render(block.to_python({
            'title': 'Joining the Lending Library',
            'body': 'Info about lending library subscription plans',
            'anchor_text': 'joining-the-lending-library',
        }))
        expected_html = '''
            <div id="joining-the-lending-library">
            <h2>Joining the Lending Library
            <a class="headerlink" href="#joining-the-lending-library"
               title="Permalink to this section">¶</a>
            </h2>
            <div class="rich-text">
                Info about lending library subscription plans
            </div>
            </div>
        '''

        self.assertHTMLEqual(html, expected_html)


class TestHomePage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        root = Page.objects.get(title='Root')
        self.assertCanCreate(root, HomePage, nested_form_data({
            'title': 'S&Co.',
            'slug': 'newhome',
            'body': streamfield([
                ('paragraph', rich_text('homepage body text')),
                ('footnotes', rich_text('homepage footnotes')),
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(HomePage, [Page])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(HomePage, [ContentLandingPage, EssayLandingPage])

    def test_template(self):
        site = Site.objects.first()
        home = HomePage.objects.first()
        response = self.client.get(home.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/home_page.html')


class TestLandingPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        # test by instantiating a non-abstract model that inherits from it
        home = HomePage.objects.first()
        self.assertCanCreate(home, ContentLandingPage, nested_form_data({
            'title': 'My Kinda Landing Page!',
            'slug': 'mylp',
            'tagline': 'now thats what im talkin about',
            'body': streamfield([
                ('paragraph', rich_text('this landing page rules')),
                ('footnotes', rich_text('footnotes to prove it, baby')),
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(
            ContentLandingPage, [HomePage])


class TestContentLandingPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        home = HomePage.objects.first()
        self.assertCanCreate(home, ContentLandingPage, nested_form_data({
            'title': 'Sources 2',
            'slug': 'sources2',
            'tagline': 'like sources, but better',
            'body': streamfield([
                ('paragraph', rich_text('the new sources landing page')),
                ('footnotes', rich_text('some landing page footnotes')),
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(ContentLandingPage, [HomePage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(ContentLandingPage, [ContentPage])

    def test_template(self):
        site = Site.objects.first()
        landing_page = ContentLandingPage.objects.get(slug="about")
        response = self.client.get(landing_page.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/landing_page.html')
        self.assertTemplateUsed(response, 'pages/content_landing_page.html')


class TestEssayLandingPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        home = HomePage.objects.first()
        self.assertCanCreate(home, EssayLandingPage, nested_form_data({
            'title': 'Analysis 2',
            'slug': 'analysis2',
            'tagline': 'do some more analysis',
            'body': streamfield([
                ('paragraph', rich_text('the second analysis landing page')),
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(EssayLandingPage, [HomePage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(EssayLandingPage, [EssayPage])

    def test_template(self):
        site = Site.objects.first()
        analysis_index = EssayLandingPage.objects.first()
        response = self.client.get(analysis_index.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/landing_page.html')
        self.assertTemplateUsed(response, 'pages/essay_landing_page.html')

    def test_get_context(self):
        analysis_index = EssayLandingPage.objects.first()
        analysis_essay = EssayPage.objects.get(slug='test-analysis')
        context = analysis_index.get_context({})
        assert 'essays' in context
        assert analysis_essay in context['essays']

        # set to not published
        analysis_essay.live = False
        analysis_essay.save()
        context = analysis_index.get_context({})
        assert analysis_essay not in context['essays']

        # TODO create some newer essays to test ordering by pub date


class TestBasePage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_get_description(self):
        '''test page preview mixin'''
        # page with body content and no description
        mypage = ContentPage(
            title='Undescribable',
            body=(
                ('paragraph', '<p>How to <a>begin</a>?</p>'),
            )
        )

        assert not mypage.description
        desc = mypage.get_description()
        # length excluding tags should be truncated to max length or less
        assert len(striptags(desc)) <= mypage.max_length
        # beginning of text should match exactly the *first* block
        # (excluding end of content because truncation is inside tags)

        # should also be cleaned by bleach to its limited set of tags
        assert desc[:200] == 'How to begin?'

        # empty tag should be stripped
        mypage.body = [('paragraph', '<p></p>')]
        desc = mypage.get_description()
        assert desc == ''

        # blockquotes should be stripped
        mypage.body = [('paragraph', '<p><blockquote>h</blockquote>i</p>')]
        desc = mypage.get_description()
        assert desc == 'hi'

        # test content page with image for first block
        mypage2 = ContentPage(
            title='What is Prosody?',
            body=[
                ('image', '<img src="milton-example.png"/>'),
                ('paragraph', '<p>Prosody today means both the study of '
                              'and <a href="#">pronunciation</a></p>'),
                ('paragraph', '<p>More content here...</p>'),
            ]
        )
        # should ignore image block and use first paragraph content
        assert mypage2.get_description()[:200] == \
            'Prosody today means both the study of and pronunciation'

        # should remove <a> tags
        assert '<a href="#">' not in mypage2.get_description()

        # should use description field when set
        intro_text = 'A short intro to prosody.'
        mypage2.description = '<p>%s</p>' % intro_text
        assert mypage2.get_description() == intro_text

        # should truncate if description content is too long
        mypage2.description = mypage.body[0]
        assert len(striptags(mypage.get_description())) \
            <= mypage.max_length


class TestContentPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        landingpage = ContentLandingPage.objects.first()
        self.assertCanCreate(landingpage, ContentPage, nested_form_data({
            'title': 'More about information',
            'slug': 'new-about',
            'body': streamfield([
                ('paragraph', rich_text('this page lives right under about'))
            ]),
            'authors-count': 0,
            'editors-count': 0
        }))

    def test_template(self):
        site = Site.objects.first()
        content_page = ContentPage.objects.get(slug="contact")
        response = self.client.get(content_page.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/base_page.html')
        self.assertTemplateUsed(response, 'pages/content_page.html')

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(ContentPage, [ContentLandingPage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(ContentPage, [])


class TestEssayPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        landingpage = EssayLandingPage.objects.first()
        self.assertCanCreate(landingpage, EssayPage, nested_form_data({
            'title': 'A new analysis esssay',
            'slug': 'new-essay',
            'body': streamfield([
                ('paragraph', rich_text('this page lives right under analysis'))
            ]),
            'authors-count': 0,
            'editors-count': 0
        }))

    def test_template(self):
        site = Site.objects.first()
        essay_page = EssayPage.objects.get(slug="test-analysis")
        response = self.client.get(essay_page.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/base_page.html')
        self.assertTemplateUsed(response, 'pages/essay_page.html')

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(EssayPage, [EssayLandingPage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(EssayPage, [])

    def test_set_url_path(self):
        # TODO
        pass
