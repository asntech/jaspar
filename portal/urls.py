## Author: Aziz Khan
## License: GPL v3
## Copyright 2017 Aziz Khan <azez.khan__AT__gmail.com>

from django.conf.urls import url
from django.conf.urls import handler404, handler500
from . import views
from jaspar import settings
from django.views.static import serve


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^search/?$', views.search, name='search'),
    url(r'^docs/$', views.documentation, name='documentation'),
    url(r'^tools/$', views.tools, name='tools'),
    url(r'^contact-us/?$', views.contact_us, name='contact_us'),
    url(r'^about/$', views.about, name='about'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^changelog/$', views.changelog, name='changelog'),
    
    #API documentation
    url(r'^api/$', views.api_documentation, name='api_documentation'),

    url(r'^inference/?$', views.profile_inference, name='profile_inference'),
    url(r'^align/?$', views.matrix_align, name='matrix_align'),
    url(r'^analysis/?$', views.analysis, name='analysis'),
    url(r'^profile-versions/?$', views.profile_versions, name='profile_versions'),
   
    url(r'^sites/(?P<matrix_id>.+)/$', views.html_binding_sites, name='html_binding_sites'),
    
    url(r'^matrix/(?P<matrix_id>[\w.]+)/$', views.matrix_detail, name='matrix_detail'),
    url(r'^matrix/(?P<base_id>\w+)/versions/$', views.matrix_versions, name='matrix_versions'),
    url(r'^matrix/(?P<matrix_id>[\w.]+)/svg/$', views.svg_logo, name='svg_logo'),

    url(r'^collection/(?P<collection>\w+)/$', views.browse_collection, name='browse_collection'),
    url(r'^cart/$', views.view_cart, name='view_cart'),
    url(r'^cart/empty$', views.empty_cart, name='empty_cart'),

    url(r'^matrix-clusters/$', views.matrix_clustering, name='matrix_clustering'),
    url(r'^matrix-clusters/(?P<tax_group>\w+)/$', views.radial_tree, name='radial_tree'),

    url(r'^genome-tracks/$', views.genome_tracks, name='genome_tracks'),

    #url redirection
    url(r'^cgi-bin/jaspar_db.pl?$', views.url_redirection, name='url_redirection'),
    url(r'^html/DOWNLOAD/?$', views.url_redirection, name='url_redirection'),

    #url(r'^news/(?P<slug>[\w-]+)/$', views.news_and_updates, name='news_and_updates'),
    url(r'^blog/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<slug>[\w-]+)$', views.post_details, name='post_details'),
    url(r'^blog/$', views.post_list, name='post_list'),

    url(r'^tour/$', views.tour_video, name='tour_video'),

    url(r'^downloads/$', views.download_data, name='download_data'),

    #enable this url to create zip/txt files for downloads page
    #url(r'^downloads-internal/$', views.internal_download_data, name='internal_download_data'),
    
    url(r'^temp/(?P<path>.*)$', serve, {'document_root': settings.TEMP_DIR}),
    url(r'^download/(?P<path>.*)$', serve, {'document_root': settings.DOWNLOAD_DIR, 'show_indexes': True,}),

]

handler404 = 'portal.views.page_not_found'
handler500 = 'portal.views.server_error'


