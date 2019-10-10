"""
mep URL Configuration
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import serve
from django.contrib import admin
from django.views.generic.base import RedirectView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps import Sitemap
from wagtail.contrib.sitemaps import views as sitemap_views
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from mep.accounts import urls as accounts_urls
from mep.books import urls as books_urls
from mep.people import urls as people_urls
from mep.footnotes import urls as footnote_urls

# sitemap configuration for sections of the site
SITEMAPS = {
    'pages': Sitemap,  # wagtail content pages
    # 'people': PeopleSitemap, # not implemented
    # 'books': BooksSitemap, # not implemented
    # 'cards': CardsSitemap, # not implemented
}

urlpatterns = [
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon/favicon.ico',
                                                permanent=True)),

    url(r'^admin/', admin.site.urls),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('pucas.cas_urls')),
    url(r'^viaf/', include('viapy.urls', namespace='viaf')),
    url(r'^', include(people_urls)),
    url(r'^', include(accounts_urls)),
    url(r'^', include(books_urls)),
    url(r'^', include(footnote_urls)),

    # sitemaps
    url(r'^sitemap\.xml$', sitemap_views.index, {'sitemaps': SITEMAPS},
        name='sitemap-index'),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap_views.sitemap,
        {'sitemaps': SITEMAPS}, name='django.contrib.sitemaps.views.sitemap'),

    # 500 error testing
    url(r'^500/$', lambda _: 1/0),

    # wagtail urls
    url(r'^cms/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'', include(wagtail_urls)),
]


# serve media content for development
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        # include debug toolbar urls first to avoid getting caught by other urls
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ] + urlpatterns
