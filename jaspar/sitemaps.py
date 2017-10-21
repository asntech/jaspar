from django.contrib import sitemaps
from django.urls import reverse

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return ['index', 'about', 'faq', 'view_cart', 'search', 'documentation','contact_us','download_data', 'tour_video', 'genome_tracks', 'matrix_clustering', 'post_list', 'profile_inference','matrix_align', 'tools', 'api_documentation']

    def location(self, item):
        return reverse(item)