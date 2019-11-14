'''
**setup_site_pages** is a custom manage command to install
a default set of pages and menus for the Wagtail CMS. It is designed not to
touch other content.

Example usage::

    python manage.py setup_site_pages
'''
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from wagtail.core.models import Page
from wagtail.core.models import Site as WagtailSite

from mep.pages.models import ContentPage, HomePage, ContentLandingPage


class Command(BaseCommand):
    '''Setup initial wagtail site and pages needed for S&co navigation'''
    help = __doc__

    #: normal verbosity level
    v_normal = 1
    verbosity = v_normal

    pages = [
        {
            'slug': 'about',
            'title': 'About',
            'tagline': 'Learn about the Shakespeare and Company Project.',
            'pages': [
                {'slug': 'contact', 'title': 'Contact Us'},
                {'slug': 'data', 'title': 'Data Export'},
                {'slug': 'cite', 'title': 'How to Cite'},
                {'slug': 'credits', 'title': 'Credits'},
                {'slug': 'technical', 'title': 'Technical'},
            ]
        },
        {
            'slug': 'sources',
            'title': 'Sources',
            'tagline': 'Learn about the lending library cards and logbooks.',
            'pages': [
                {'slug': 'cards', 'title': 'Lending Library Cards'},
                {'slug': 'logbooks', 'title': 'Logbooks'},
            ]
        }
    ]

    def handle(self, *args, **_kwargs):
        # NOTE: logic for creating pages based on wagtail core migration
        # 0002 initial data, which creates initial site and welcome page

        # delete default home wagtail home page
        Page.objects.filter(slug='home', title__contains='Welcome').delete()

        # Create S&Co. homepage
        home = HomePage.objects.filter(slug='home').first()
        if not home:
            home = HomePage.objects.create(
                title='Shakespeare & Company Project',
                slug='home',
                depth=2,
                numchild=0,
                show_in_menus=True,
                path='00010001',
                content_type=ContentType.objects.get_for_model(HomePage),
            )

        # Create landing pages
        for i, page in enumerate(self.pages):
            landing_page = Page.objects.filter(slug=page['slug']).first()
            if not landing_page:
                landing_page = ContentLandingPage.objects.create(
                    title=page['title'],
                    slug=page['slug'],
                    tagline=page['tagline'],
                    depth=3,
                    path='{}{:04d}'.format(home.path, i),
                    show_in_menus=True,
                    content_type=ContentType.objects.get_for_model(ContentLandingPage)
                )
            # Create subpages for each landing page
            for i_, page_ in enumerate(page['pages']):
                content_page = Page.objects.filter(slug=page_['slug']).first()
                if not content_page:
                    ContentPage.objects.create(
                        title=page_['title'],
                        slug=page_['slug'],
                        depth=4,
                        path='{}{:04d}'.format(landing_page.path, i_),
                        show_in_menus=True,
                        content_type=ContentType.objects.get_for_model(ContentPage)
                    )

        # create wagtail site from django site and associate new homepage
        self.create_wagtail_site(home.page_ptr)

        # let treebeard fix the hierarchy
        Page.fix_tree()

    def create_wagtail_site(self, root_page):
        '''Create a wagtail site object from the current default
        Django site.'''
        current_site = Site.objects.get(pk=settings.SITE_ID)

        # split domain into name and port
        if ':' in current_site.domain:
            domain, port = current_site.domain.split(':')
        else:
            domain = current_site.domain
            port = 80

        # create wagtail site with same config and associate home page
        wagtail_site, _created = WagtailSite.objects.get_or_create(
            hostname=domain,
            port=port,
            site_name=current_site.name,
            root_page=root_page,
            is_default_site=True)

        return wagtail_site
