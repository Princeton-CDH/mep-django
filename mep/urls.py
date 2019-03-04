"""
mep URL Configuration
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import serve
from django.contrib import admin
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
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('pucas.cas_urls')),
    url(r'^viaf/', include('viapy.urls', namespace='viaf')),
    url(r'^', include(people_urls, namespace='people')),
    url(r'^', include(accounts_urls, namespace='accounts')),
    url(r'^', include(books_urls, namespace='books')),
    url(r'^', include(footnote_urls, namespace='footnotes')),

    # sitemaps
    url(r'^sitemap\.xml$', sitemap_views.index, {'sitemaps': SITEMAPS},
        name='sitemap-index'),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap_views.sitemap,
        {'sitemaps': SITEMAPS}, name='django.contrib.sitemaps.views.sitemap'),

    # wagtail urls
    url(r'^cms/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'', include(wagtail_urls)),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)), # debug toolbar
        url(r'^media/(?P<path>.*)$', serve, { # uploaded media
            'document_root': settings.MEDIA_ROOT
        })
    ]
