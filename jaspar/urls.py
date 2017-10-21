## Author: Aziz Khan
## License: GPL v3
## Copyright 2017 Aziz Khan <azez.khan__AT__gmail.com>


"""jaspar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from rest_framework.documentation import include_docs_urls

from rest_framework.schemas import get_schema_view

# from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
# schema_view = get_schema_view(
#     title='JASPAR API',
#     #renderer_classes=[OpenAPIRenderer, SwaggerUIRenderer]
# )

from rest_framework_swagger.views import get_swagger_view
schema_view = get_swagger_view(title='JASPAR REST Live API')

from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
}

admin.site.site_header = 'JASPAR Admin'

urlpatterns = [
    url(r'^', include('portal.urls')),

    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/', include('restapi.v1.urls', namespace='v1')),
    #url(r'^api/current/', include('restapi.v1.urls', namespace='current')),
    url(r'^$', schema_view),
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/doc/', include_docs_urls(title='JASPAR RESTful API')),
    url(r'^api/v1/live/', schema_view),

    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),

]




if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns


