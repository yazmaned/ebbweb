import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.conf import settings
from .models import Material, Category
from accounts.models import SessionLog, Journal
from django.http import HttpResponse

def robots_txt(request):
    content = """User-agent: *
Allow: /
Allow: /journal/
Allow: /about/
Allow: /home/

Disallow: /dashboard/
Disallow: /muthisadmin/
Disallow: /portal/
Disallow: /accounts/
Disallow: /file/
Disallow: /video/

Sitemap: https://bilgehanhoca.com/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')

def home(request):
    journals = Journal.objects.filter(is_active=True, show_on_home=True, is_seo=False)[:5]
    if request.user.is_authenticated:
        SessionLog.objects.filter(user=request.user, is_active=True).update(current_material='Ana Sayfa')
    return render(request, 'content/home.html', {'journals': journals})

def journal_archive(request):
    journals = Journal.objects.filter(is_active=True, is_seo=False)
    seo_journals = Journal.objects.filter(is_active=True, is_seo=True)
    return render(request, 'content/journal_archive.html', {
        'journals': journals,
        'seo_journals': seo_journals,
    })

def about(request):
    return render(request, 'content/about.html')

@login_required
def add_journal(request):
    if request.user.username != 'bilge':
        return redirect('/home/')
    if request.method == 'POST':
        title = request.POST.get('title').strip()
        body = request.POST.get('body').strip()
        image = request.FILES.get('image')
        show_on_home = 'only_archive' not in request.POST
        show_timestamp = 'hide_timestamp' not in request.POST
        is_seo = 'is_seo' in request.POST
        Journal.objects.create(
            title=title,
            body=body,
            image=image,
            show_on_home=show_on_home,
            show_timestamp=show_timestamp,
            is_seo=is_seo,
        )
        return redirect('/home/')
    return render(request, 'content/add_journal.html')

@login_required
def delete_journal(request, pk):
    if request.user.username != 'bilge':
        return redirect('/home/')
    Journal.objects.filter(pk=pk).delete()
    return redirect('/home/')

def view_journal(request, slug):
    journal = get_object_or_404(Journal, slug=slug)
    return render(request, 'content/journal_detail.html', {'journal': journal})

@login_required
def dashboard(request):
    root_categories = Category.objects.filter(parent=None).prefetch_related(
        'children', 'children__children', 'children__materials',
        'materials', 'children__children__materials'
    )
    uncategorized = Material.objects.filter(category=None)
    SessionLog.objects.filter(user=request.user, is_active=True).update(current_material='Dashboard')
    return render(request, 'content/dashboard.html', {
        'root_categories': root_categories,
        'uncategorized': uncategorized,
    })

@login_required
def serve_file(request, pk):
    material = get_object_or_404(Material, pk=pk)
    file_path = os.path.join(settings.MEDIA_ROOT, material.file.name)
    if not os.path.exists(file_path):
        raise Http404
    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{material.title}.pdf"'
    return response

@login_required
def view_pdf(request, pk):
    material = get_object_or_404(Material, pk=pk)
    SessionLog.objects.filter(user=request.user, is_active=True).update(
        current_material=f'📄 {material.title}'
    )
    return render(request, 'content/pdf_viewer.html', {'material': material})

@login_required
def view_video(request, pk):
    material = get_object_or_404(Material, pk=pk)
    SessionLog.objects.filter(user=request.user, is_active=True).update(
        current_material=f'🎥 {material.title}'
    )
    return render(request, 'content/video_viewer.html', {'material': material})