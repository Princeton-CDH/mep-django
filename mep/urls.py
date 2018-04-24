"""
mep URL Configuration
"""
import mezzanine.urls
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import render
from django.views.generic.base import RedirectView, TemplateView

from mep.accounts import urls as accounts_urls
from mep.books import urls as books_urls
from mep.people import urls as people_urls

# use test favicon when test warning is enabled as another visual indicator
FAVICON = '/static/favicon.ico'
if getattr(settings, 'SHOW_TEST_WARNING', False):
    FAVICON = '/static/favicon-test.ico'

urlpatterns = [
    url(r'robots\.txt$', lambda request:
        render(request, 'robots.txt',
        content_type='text/plain', context={'DEBUG': settings.DEBUG})),
    url(r'^favicon\.ico$', RedirectView.as_view(url=FAVICON, permanent=True)),
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('pucas.cas_urls')),
    url(r'^viaf/', include('viapy.urls', namespace='viaf')),
    url(r'^members/', include(people_urls, namespace='members')),
    url(r'^accounts/', include(accounts_urls, namespace='accounts')),
    url(r'^books/', include(books_urls, namespace='books')),

    # content pages managed by mezzanine
    url(r'^', include(mezzanine.urls))
]
