"""
mep URL Configuration
"""
from django.conf import settings
from django.urls import re_path, path, include
from django.conf.urls.static import serve
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps import Sitemap as WagtailSitemap
from wagtail.contrib.sitemaps import views as sitemap_views
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from mep.accounts import urls as accounts_urls
from mep.books import urls as books_urls
from mep.books import sitemaps as book_sitemaps
from mep.footnotes import urls as footnote_urls
from mep.people import sitemaps as member_sitemaps
from mep.people import urls as people_urls


# sitemap configuration for sections of the site
SITEMAPS = {
    "pages": WagtailSitemap,  # wagtail content pages
    # member pages
    "members": member_sitemaps.MemberSitemap,
    "member-activities": member_sitemaps.MembershipActivitiesSitemap,
    "member-borrowing": member_sitemaps.BorrowingActivitiesSitemap,
    "member-card-list": member_sitemaps.MemberCardListSitemap,
    "member-card-detail": member_sitemaps.MemberCardDetailSitemap,
    # book pages
    "books": book_sitemaps.BookSitemap,
    "book-circulation": book_sitemaps.BookCirculationSitemap,
    "book-card-list": book_sitemaps.BookCardListSitemap,
}

urlpatterns = [
    re_path(
        r"^robots\.txt$",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    re_path(
        r"^favicon\.ico$",
        RedirectView.as_view(url="/static/favicon/favicon.ico", permanent=True),
    ),
    path("admin/", admin.site.urls),
    path("grappelli/", include("grappelli.urls")),
    path("accounts/", include("pucas.cas_urls")),
    path("viaf/", include("viapy.urls", namespace="viaf")),
    re_path(r"^", include(people_urls)),
    re_path(r"^", include(accounts_urls)),
    re_path(r"^", include(books_urls)),
    re_path(r"^", include(footnote_urls)),
    # sitemaps
    re_path(
        r"^sitemap\.xml$",
        sitemap_views.index,
        {"sitemaps": SITEMAPS},
        name="sitemap-index",
    ),
    re_path(
        r"^sitemap-(?P<section>.+)\.xml$",
        sitemap_views.sitemap,
        {"sitemaps": SITEMAPS},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # wagtail urls
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    re_path(r"", include(wagtail_urls)),
    # direct 500 access for testing
    re_path(r"^_500$", lambda _: 1 / 0),
]


# serve media content for development
if settings.DEBUG:
    try:
        import debug_toolbar

        # add debug toolbar urls first to avoid getting caught by other urls
        urlpatterns.insert(0, re_path(r"^__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass

    urlpatterns.append(
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {
                "document_root": settings.MEDIA_ROOT,
            },
        )
    )
