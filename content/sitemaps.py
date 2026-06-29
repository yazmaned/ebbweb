from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from accounts.models import Journal

class HomeSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)

class JournalSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Journal.objects.filter(is_active=True, is_seo=False).order_by('-created_at')

    def location(self, obj):
        return f'/journal/{obj.slug}/'

    def lastmod(self, obj):
        return obj.created_at

class SeoJournalSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return Journal.objects.filter(is_active=True, is_seo=True).order_by('-created_at')

    def location(self, obj):
        return f'/journal/{obj.slug}/'

    def lastmod(self, obj):
        return obj.created_at

class StaticSitemap(Sitemap):
    pages = {
        'journal_archive': (0.6, 'weekly'),
        'about': (0.5, 'monthly'),
        'score_calculator': (0.7, 'monthly'),
        'mini_quiz': (0.6, 'monthly'),
    }

    def items(self):
        return list(self.pages.keys())

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.pages[item][0]

    def changefreq(self, item):
        return self.pages[item][1]