from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from accounts.models import Journal

class JournalSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Journal.objects.filter(is_active=True)

    def location(self, obj):
        return f'/journal/{obj.slug}/'

    def lastmod(self, obj):
        return obj.created_at

class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return ['home', 'journal_archive', 'about']

    def location(self, item):
        return reverse(item)