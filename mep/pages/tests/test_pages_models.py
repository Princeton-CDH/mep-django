import bleach
from django.template.defaultfilters import striptags, truncatechars_html
from wagtail.core.models import Page, Site
from wagtail.tests.utils import WagtailPageTests
from wagtail.tests.utils.form_data import (nested_form_data, rich_text,
                                           streamfield)

from mep.pages.models import (ContentPage, HomePage, LandingPage,
                              RoutableLandingPage)


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
        self.assertAllowedSubpageTypes(HomePage, [LandingPage, RoutableLandingPage])

    def test_template(self):
        site = Site.objects.first()
        home = HomePage.objects.first()
        response = self.client.get(home.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/home_page.html')


class TestLandingPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        home = HomePage.objects.first()
        self.assertCanCreate(home, LandingPage, nested_form_data({
            'title': 'Sources 2',
            'slug': 'sources2',
            'tagline': 'like sources, but better',
            'body': streamfield([
                ('paragraph', rich_text('the new sources landing page')),
                ('footnotes', rich_text('some landing page footnotes')),
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(LandingPage, [HomePage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(LandingPage, [ContentPage])

    def test_template(self):
        site = Site.objects.first()
        landing_page = LandingPage.objects.get(slug="about")
        response = self.client.get(landing_page.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/landing_page.html')


class TestRoutableLandingPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        home = HomePage.objects.first()
        self.assertCanCreate(home, RoutableLandingPage, nested_form_data({
            'title': 'Analysis 2',
            'slug': 'analysis2',
            'tagline': 'do some more analysis',
            'body': streamfield([
                ('paragraph', rich_text('the second analysis landing page')),
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(RoutableLandingPage, [HomePage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(RoutableLandingPage, [ContentPage])

    def test_template(self):
        site = Site.objects.first()
        analysis_index = RoutableLandingPage.objects.first()
        response = self.client.get(analysis_index.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/landing_page.html')
        self.assertTemplateUsed(response, 'pages/routable_landing_page.html')

    def test_get_context(self):
        analysis_index = RoutableLandingPage.objects.first()
        analysis_essay = ContentPage.objects.get(title='Test analysis')
        context = analysis_index.get_context({})
        assert 'posts' in context
        assert analysis_essay in context['posts']

        # set to not published
        analysis_essay.live = False
        analysis_essay.save()
        context = analysis_index.get_context({})
        assert analysis_essay not in context['posts']

        # TODO create some newer essays to test ordering by pub date


class TestContentPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        landing_page = LandingPage.objects.first()
        self.assertCanCreate(landing_page, ContentPage, nested_form_data({
            'title': 'A newly discovered content source',
            'slug': 'new-source',
            'body': streamfield([
                ('paragraph', rich_text('this page lives under sources'))
            ]),
            'authors-count': 0,
            'editors-count': 0
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(ContentPage, [LandingPage, RoutableLandingPage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(ContentPage, [])

    def test_template(self):
        site = Site.objects.first()
        # test with a standard page, not an analysis ocntent page
        content_page = ContentPage.objects.get(slug="contact")
        response = self.client.get(content_page.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/content_page.html')

    def test_get_description(self):
        '''test page preview mixin'''
        # page with body content and no description
        content_page = ContentPage(
            title='Undescribable',
            body=[
                ('paragraph', '<p>How to <a>begin</a>?</p>'),
            ]
        )

        assert not content_page.description
        desc = content_page.get_description()
        # length excluding tags should be truncated to max length or less
        assert len(striptags(desc)) <= content_page.max_length
        # beginning of text should match exactly the *first* block
        # (excluding end of content because truncation is inside tags)

        # should also be cleaned by bleach to its limited set of tags
        assert desc[:200] == 'How to begin?'

        # empty tag should be stripped
        content_page.body = [('paragraph', '<p></p>')]
        desc = content_page.get_description()
        assert desc == ''

        # blockquotes should be stripped
        content_page.body = [('paragraph', '<p><blockquote>h</blockquote>i</p>')]
        desc = content_page.get_description()
        assert desc == 'hi'

        # test content page with image for first block
        content_page2 = ContentPage(
            title='What is Prosody?',
            body=[
                ('image', '<img src="milton-example.png"/>'),
                ('paragraph', '<p>Prosody today means both the study of '
                              'and <a href="#">pronunciation</a></p>'),
                ('paragraph', '<p>More content here...</p>'),
            ]
        )
        # should ignore image block and use first paragraph content
        assert content_page2.get_description()[:200] == \
            'Prosody today means both the study of and pronunciation'

        # should remove <a> tags
        assert '<a href="#">' not in content_page2.get_description()

        # should use description field when set
        intro_text = 'A short intro to prosody.'
        content_page2.description = '<p>%s</p>' % intro_text
        assert content_page2.get_description() == intro_text

        # should truncate if description content is too long
        content_page2.description = content_page.body[0]
        assert len(striptags(content_page.get_description())) \
            <= content_page.max_length
