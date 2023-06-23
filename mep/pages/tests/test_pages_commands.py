from django.contrib.sites.models import Site
from django.test import TestCase
from wagtail.core.models import Page

from mep.pages.management.commands import setup_site_pages
from mep.pages.models import ContentLandingPage, ContentPage, EssayLandingPage, HomePage


class TestSetupSitePagesCommand(TestCase):
    def setUp(self):
        self.cmd = setup_site_pages.Command()

    def test_create_wagtail_site(self):
        root_page = Page.objects.first()
        # test with existing example.com default site first
        wagtail_site = self.cmd.create_wagtail_site(root_page)

        # port should be inferred when not present in domain
        site = Site.objects.first()
        assert wagtail_site.hostname == site.domain
        assert wagtail_site.port == 80
        assert wagtail_site.site_name == site.name
        assert wagtail_site.root_page == root_page
        assert wagtail_site.is_default_site

        # port should be split out when present
        site.domain = "localhost:8000"
        site.save()
        wagtail_site = self.cmd.create_wagtail_site(root_page)
        assert wagtail_site.hostname == "localhost"
        assert wagtail_site.port == "8000"

    def test_create_pages(self):
        self.cmd.handle()

        assert not Page.objects.filter(
            slug="home", title__contains="Welcome"
        ).count(), "should delete welcome page"

        assert HomePage.objects.count() == 1, "should create 1 homepage"

        assert (
            ContentLandingPage.objects.count() == 2
        ), "should create sources and about landing page"

        assert (
            EssayLandingPage.objects.count() == 1
        ), "should create analysis landing page"

        assert ContentPage.objects.count() == 8, "should create 8 content pages"

        self.cmd.handle()  # run again

        assert (
            HomePage.objects.count() == 1
        ), "running twice shouldn't duplicate homepage"

        assert (
            ContentLandingPage.objects.count() == 2
        ), "running twice shouldn't create duplicate landing pages"

        assert (
            EssayLandingPage.objects.count() == 1
        ), "running twice shouldn't create duplicate landing pages"

        assert (
            ContentPage.objects.count() == 8
        ), "running twice shouldn't \
            create duplicate content pages"
