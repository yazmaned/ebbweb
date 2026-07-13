import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.conf import settings
from django.db.models import Q
from .models import Material, Category
from accounts.models import SessionLog, Journal
from django.http import HttpResponse
from accounts.models import SessionLog, Journal, UserProfile
from django.http import JsonResponse

from .models import Material, Category, CarouselItem


# Bilge and yazman (admin/superuser teacher accounts) always see every
# active-course folder, regardless of allowed_users — but they're never
# listed as selectable students in the portal picker either.
PRIVILEGED_USERNAMES = ('bilge', 'yazman')


def _is_privileged(user):
    return user.username in PRIVILEGED_USERNAMES


def _visible_categories_q(user):
    """A category is hidden unless it's not an active-course folder,
    this user is explicitly on its allowed list, or this user is privileged."""
    if _is_privileged(user):
        return Q()
    return Q(is_active_course=False) | Q(is_active_course=True, allowed_users=user)


def home(request):
    journals = Journal.objects.filter(is_active=True, show_on_home=True, is_seo=False)[:4]
    carousel = CarouselItem.objects.filter(is_active=True)
    context = {'journals': journals, 'carousel': carousel}

    if request.user.is_authenticated:
        SessionLog.objects.filter(user=request.user, is_active=True).update(current_material='Ana Sayfa')
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        context['user_profile'] = profile

    return render(request, 'content/home.html', context)

def score_calculator(request):
    return render(request, 'content/calculator.html')

def robots_txt(request):
    content = """User-agent: *
Allow: /
Allow: /journal/
Allow: /about/
Allow: /home/
Allow: /hesaplama/
Allow: /quiz/
Allow: /quiz/mini/

Disallow: /dashboard/
Disallow: /muthisadmin/
Disallow: /portal/
Disallow: /accounts/
Disallow: /file/
Disallow: /video/
Disallow: /quiz/result/
Disallow: /quiz/full/

Sitemap: https://bilgehanhoca.com/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')

def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

def journal_archive(request):
    journals = Journal.objects.filter(is_active=True, is_seo=False)
    seo_journals = Journal.objects.filter(is_active=True, is_seo=True)
    return render(request, 'content/journal_archive.html', {
        'journals': journals,
        'seo_journals': seo_journals,
    })

def construction(request):
    return render(request, 'content/construction.html')

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
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.has_library_access:
        return redirect('/home/')

    if _is_privileged(request.user):
        active_course = Category.objects.filter(is_active_course=True, parent=None).first()
    else:
        active_course = Category.objects.filter(
            is_active_course=True, parent=None, allowed_users=request.user
        ).first()

    root_categories = Category.objects.filter(parent=None).filter(
        _visible_categories_q(request.user)
    ).exclude(
        pk=active_course.pk if active_course else None
    ).distinct().prefetch_related(
        'children', 'children__children', 'children__materials',
        'materials', 'children__children__materials'
    )
    uncategorized = Material.objects.filter(category=None)

    video_count = Material.objects.filter(material_type__in=['video', 'youtube', 'vimeo']).count()
    material_count = Material.objects.filter(material_type__in=['pdf', 'image']).count()

    SessionLog.objects.filter(user=request.user, is_active=True).update(current_material='Dashboard')
    return render(request, 'content/dashboard.html', {
        'root_categories': root_categories,
        'uncategorized': uncategorized,
        'video_count': video_count,
        'material_count': material_count,
        'active_course': active_course,
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

@login_required
def serve_image(request, pk):
    material = get_object_or_404(Material, pk=pk)
    file_path = os.path.join(settings.MEDIA_ROOT, material.file.name)
    if not os.path.exists(file_path):
        raise Http404
    ext = material.file.name.lower().rsplit('.', 1)[-1]
    content_type = 'image/png' if ext == 'png' else 'image/jpeg'
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{material.title}.{ext}"'
    return response

@login_required
def view_image(request, pk):
    material = get_object_or_404(Material, pk=pk)
    SessionLog.objects.filter(user=request.user, is_active=True).update(
        current_material=f'Görsel: {material.title}'
    )
    return render(request, 'content/image_viewer.html', {'material': material})

@login_required
def dashboard_explorer(request):
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.has_library_access:
        return redirect('/home/')

    category_id = request.GET.get('category')
    current_category = None
    if category_id:
        current_category = get_object_or_404(Category, pk=category_id)
        if (current_category.is_active_course
                and not _is_privileged(request.user)
                and not current_category.allowed_users.filter(pk=request.user.pk).exists()):
            return redirect('/dashboard/explorer/')

    subfolders = Category.objects.filter(parent=current_category).filter(
        _visible_categories_q(request.user)
    ).distinct().order_by('order', 'name')
    files = Material.objects.filter(category=current_category).order_by('order', 'title')

    breadcrumbs = []
    node = current_category
    while node is not None:
        breadcrumbs.insert(0, node)
        node = node.parent

    video_count = Material.objects.filter(material_type__in=['video', 'youtube', 'vimeo']).count()
    material_count = Material.objects.filter(material_type__in=['pdf', 'image']).count()

    SessionLog.objects.filter(user=request.user, is_active=True).update(current_material='Dashboard (Explorer)')

    return render(request, 'content/dashboard_explorer.html', {
        'current_category': current_category,
        'subfolders': subfolders,
        'files': files,
        'breadcrumbs': breadcrumbs,
        'video_count': video_count,
        'material_count': material_count,
    })

@login_required
def dashboard_explorer_data(request):
    """AJAX companion to dashboard_explorer — same queries, JSON instead of a template."""
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.has_library_access:
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    category_id = request.GET.get('category')
    current_category = None
    if category_id:
        current_category = get_object_or_404(Category, pk=category_id)
        if (current_category.is_active_course
                and not _is_privileged(request.user)
                and not current_category.allowed_users.filter(pk=request.user.pk).exists()):
            return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    subfolders = Category.objects.filter(parent=current_category).filter(
        _visible_categories_q(request.user)
    ).distinct().order_by('order', 'name')
    files = Material.objects.filter(category=current_category).order_by('order', 'title')

    breadcrumbs = []
    node = current_category
    while node is not None:
        breadcrumbs.insert(0, node)
        node = node.parent

    SessionLog.objects.filter(user=request.user, is_active=True).update(current_material='Dashboard (Explorer)')

    def open_url_for(material):
        if material.material_type == 'pdf':
            return f'/view/{material.pk}/'
        elif material.material_type == 'image':
            return f'/image/{material.pk}/'
        else:
            return f'/video/{material.pk}/'

    return JsonResponse({
        'ok': True,
        'category_id': current_category.pk if current_category else None,
        'subfolders': [{'id': f.pk, 'name': f.name} for f in subfolders],
        'files': [
            {'id': m.pk, 'title': m.title, 'material_type': m.material_type, 'open_url': open_url_for(m)}
            for m in files
        ],
        'breadcrumbs': [{'id': c.pk, 'name': c.name} for c in breadcrumbs],
    })

@login_required
def dashboard_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    def breadcrumb_path(category):
        names = []
        node = category
        while node is not None:
            names.insert(0, node.name)
            node = node.parent
        return ' / '.join(names) if names else 'Kütüphane'

    def material_visible(material):
        if material.category and material.category.is_active_course:
            if _is_privileged(request.user):
                return True
            return material.category.allowed_users.filter(pk=request.user.pk).exists()
        return True

    results = []

    for material in Material.objects.filter(title__icontains=query).select_related('category')[:50]:
        if not material_visible(material):
            continue

        if material.material_type == 'pdf':
            open_url = f'/view/{material.pk}/'
        elif material.material_type == 'image':
            open_url = f'/image/{material.pk}/'
        else:
            open_url = f'/video/{material.pk}/'

        results.append({
            'type': 'material',
            'id': material.pk,
            'name': material.title,
            'material_type': material.material_type,
            'path': breadcrumb_path(material.category),
            'open_url': open_url,
            'navigate_to': material.category.pk if material.category else '',
        })

    for category in Category.objects.filter(name__icontains=query).filter(
        _visible_categories_q(request.user)
    ).distinct()[:50]:
        results.append({
            'type': 'category',
            'id': category.pk,
            'name': category.name,
            'path': breadcrumb_path(category.parent),
            'navigate_to': category.pk,
        })

    return JsonResponse({'results': results})