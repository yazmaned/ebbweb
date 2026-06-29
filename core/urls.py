from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from content.sitemaps import JournalSitemap, StaticSitemap


admin.site.site_header = "Bilge Dil Admin Paneli"
admin.site.site_title = "BD Admin"
admin.site.index_title = "Welcome, Bilgehan 💛"

handler404 = 'content.views.error_404'
handler500 = 'content.views.error_500'

from content.sitemaps import HomeSitemap, JournalSitemap, SeoJournalSitemap, StaticSitemap

sitemaps = {
    'home': HomeSitemap,
    'journals': JournalSitemap,
    'seo_journals': SeoJournalSitemap,
    'static': StaticSitemap,
}

urlpatterns = [
    path('muthisadmin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('portal/', include('portal.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', include('content.urls')),
    path('quiz/', include('quiz.urls')),
    path('', RedirectView.as_view(url='/home/')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)