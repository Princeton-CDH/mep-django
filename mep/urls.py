"""
mep URL Configuration
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
import mezzanine.urls

from mep.people import urls as people_urls
from mep.accounts import urls as accounts_urls
from mep.books import urls as books_urls
from mep.common.views import Homepage, About

urlpatterns = [
    # for now, since wagtail isn't implemented, redirect base url to a simple
    # homepage view and '/about' to a simple about page view
    url(r'^$', Homepage.as_view(), name='home'),
    url(r'^about/$', About.as_view(), name='about'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('pucas.cas_urls')),
    url(r'^viaf/', include('viapy.urls', namespace='viaf')),
    url(r'^', include(people_urls, namespace='people')),
    url(r'^', include(accounts_urls, namespace='accounts')),
    url(r'^', include(books_urls, namespace='books')),

    # content pages managed by mezzanine
    url(r'^', include(mezzanine.urls))
]

