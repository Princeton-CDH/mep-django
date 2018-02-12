"""
mep URL Configuration
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
import mezzanine.urls

urlpatterns = [
    # for now, since there is not yet any public-facing site,
    # redirect base url to admin index page
    url(r'^$', RedirectView.as_view(pattern_name='admin:index'), name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('pucas.cas_urls')),
    url(r'^viaf/', include('viapy.urls', namespace='viaf')),
    url(r'^', include('mep.people.urls', namespace='people')),
    url(r'^', include('mep.accounts.urls', namespace='accounts')),

    # content pages managed by mezzanine
    url(r'^', include(mezzanine.urls))
]

