# -*- coding: utf-8 -*-
## Author: Aziz Khan
## License: GPL v3
## Copyright © 2017 Aziz Khan <azez.khan__AT__gmail.com>

from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from django.views.decorators.cache import cache_page

from . import views

#cache timeout in seconds

CACHE_TIMEOUT = 60 * 60  #24 hours
#CACHE_TIMEOUT = 0


urlpatterns = [
	#url(r'^$', cache_page(CACHE_TIMEOUT)(views.APIRoot.as_view()), name='api-root'),
	url(r'^$', views.APIRoot.as_view(), name='api-root'),

    url(r'^matrix/?$', views.MatrixListViewSet.as_view(), name='matrix-list'),
    url(r'^matrix/(?P<base_id>\w+)/versions/$', views.MatrixVersionsViewSet.as_view(), name='matrix-versions'),
    url(r'^matrix/(?P<matrix_id>.+)/$', views.MatrixDetailsViewSet.as_view(), name='matrix-detail'),
    url(r'^collection/(?P<collection>\w+)/$', views.CollectionMatrixListViewSet.as_view(), name='collection'),
    #url(r'^matrix/(?P<collection>\w+)/collection/$', views.CollectionMatrixListViewSet.as_view(), name='collection'),
    url(r'^infer/(?P<sequence>\w+)/$', views.MatrixInferenceViewSet.as_view(), name='matrix-infer'),
    #url(r'^align/(?P<sequence>\w+)/$', views.MatrixAlignViewSet.as_view(), name='matrix-align'),

    #url(r'^live/', include('rest_framework_docs.urls')),
    url(r'^home/?$', views.api_homepage, name='api-homepage'),
    url(r'^docs/?$', views.api_docs, name='api-docs'),
    url(r'^overview/?$', views.api_overview, name='api-overview'),
    url(r'^clients/?$', views.api_clients, name='api-clients'),

    
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json','jsonp','jaspar','meme','pfm','transfac','yaml','api'])