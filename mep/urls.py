"""mep URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

urlpatterns = [
    # for now, since there is not yet any public-facing site,
    # redirect base url to admin index page
    url(r'^$', RedirectView.as_view(pattern_name='admin:index'), name='site-index'),
    url(r'^admin/', admin.site.urls),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('pucas.cas_urls')),
    url(r'^viaf/', include('viapy.urls', namespace='viaf')),
    url(r'^', include('mep.people.urls', namespace='people')),
]
