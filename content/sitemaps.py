from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from accounts.models import Journal

class JournalSitemap(Sitemap):
    changefreq = 'always'
    priority = 0.8

    def items(self):
        return Journal.objects.filter(is_active=True)

    def location(self, obj):
        return f'/journal/{obj.slug}/'

    def lastmod(self, obj):
        return obj.created_at

class StaticSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.5

    def items(self):
        return ['home','journal_archive', 'score_calculator']

    def location(self, item):
        return reverse(item)
    
class Homemap(Sitemap):
    changefreq = 'Daily'
    priority = 1

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)