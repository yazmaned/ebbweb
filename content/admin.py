import os
import re
import re as re_module
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.files.base import ContentFile

from .models import Material, Category, CarouselItem

PDF_EXTENSIONS = {'.pdf'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


@admin.register(CarouselItem)
class CarouselItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'order')
    list_editable = ('order',)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'material_type', 'category', 'order', 'uploaded_at')
    list_filter = ('material_type', 'category')
    list_editable = ('order',)
    search_fields = ('title',)
    change_list_template = 'admin/content/material/change_list.html'

    def get_urls(self):
        custom_urls = [
            path('explorer/', self.admin_site.admin_view(self.explorer_view), name='content_material_explorer'),
            path('explorer/move/', self.admin_site.admin_view(self.explorer_move), name='content_material_explorer_move'),
            path('explorer/create-folder/', self.admin_site.admin_view(self.explorer_create_folder), name='content_material_explorer_create_folder'),
            path('explorer/rename/', self.admin_site.admin_view(self.explorer_rename), name='content_material_explorer_rename'),
            path('explorer/delete/', self.admin_site.admin_view(self.explorer_delete), name='content_material_explorer_delete'),
            path('explorer/upload/', self.admin_site.admin_view(self.explorer_upload), name='content_material_explorer_upload'),
            path('explorer/add-vimeo/', self.admin_site.admin_view(self.explorer_add_vimeo), name='content_material_explorer_add_vimeo'),
            path('explorer/search/', self.admin_site.admin_view(self.explorer_search), name='content_material_explorer_search'),
        ]
        return custom_urls + super().get_urls()

    # ---------- Main page ----------

    def explorer_view(self, request):
        category_id = request.GET.get('category')
        current_category = None
        if category_id:
            current_category = get_object_or_404(Category, pk=category_id)

        subfolders = Category.objects.filter(parent=current_category).order_by('order', 'name')
        files = Material.objects.filter(category=current_category).order_by('order', 'title')

        breadcrumbs = []
        node = current_category
        while node is not None:
            breadcrumbs.insert(0, node)
            node = node.parent

        context = dict(
            self.admin_site.each_context(request),
            current_category=current_category,
            subfolders=subfolders,
            files=files,
            breadcrumbs=breadcrumbs,
        )
        return render(request, 'admin/content/material/explorer.html', context)

    # ---------- AJAX: move (drag & drop) ----------

    def explorer_move(self, request):
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')
        target_id = request.POST.get('target_category_id')  # '' or 'null' means root

        target_category = None
        if target_id and target_id not in ('null', ''):
            target_category = get_object_or_404(Category, pk=target_id)

        if item_type == 'material':
            material = get_object_or_404(Material, pk=item_id)
            material.category = target_category
            material.save()
            return JsonResponse({'ok': True})

        elif item_type == 'category':
            category = get_object_or_404(Category, pk=item_id)

            if target_category is not None:
                if target_category.pk == category.pk:
                    return JsonResponse({'ok': False, 'error': 'A folder cannot be moved into itself.'}, status=400)
                # Prevent moving a folder into one of its own descendants —
                # walk up from the target and make sure we never hit `category`.
                node = target_category
                while node is not None:
                    if node.pk == category.pk:
                        return JsonResponse({'ok': False, 'error': 'Cannot move a folder into its own subfolder.'}, status=400)
                    node = node.parent

            category.parent = target_category
            category.save()
            return JsonResponse({'ok': True})

        return JsonResponse({'ok': False, 'error': 'Unknown item type.'}, status=400)

    # ---------- AJAX: create folder ----------

    def explorer_create_folder(self, request):
        name = request.POST.get('name', '').strip()
        parent_id = request.POST.get('parent_id')
        if not name:
            return JsonResponse({'ok': False, 'error': 'Folder name cannot be empty.'}, status=400)

        parent = None
        if parent_id and parent_id not in ('null', ''):
            parent = get_object_or_404(Category, pk=parent_id)

        category, created = Category.objects.get_or_create(name=name, parent=parent)
        return JsonResponse({'ok': True, 'id': category.pk, 'created': created})

    # ---------- AJAX: rename ----------

    def explorer_rename(self, request):
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')
        new_name = request.POST.get('new_name', '').strip()

        if not new_name:
            return JsonResponse({'ok': False, 'error': 'Name cannot be empty.'}, status=400)

        if item_type == 'material':
            material = get_object_or_404(Material, pk=item_id)
            material.title = new_name
            material.save()
        elif item_type == 'category':
            category = get_object_or_404(Category, pk=item_id)
            category.name = new_name
            category.save()
        else:
            return JsonResponse({'ok': False, 'error': 'Unknown item type.'}, status=400)

        return JsonResponse({'ok': True})

    # ---------- AJAX: delete ----------

    def explorer_delete(self, request):
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')

        if item_type == 'material':
            Material.objects.filter(pk=item_id).delete()
        elif item_type == 'category':
            # Category.parent uses on_delete=CASCADE, so deleting a folder
            # also deletes every subfolder and material inside it — this is
            # the expected "delete folder and everything in it" behavior,
            # but it's worth knowing there's no undo.
            Category.objects.filter(pk=item_id).delete()
        else:
            return JsonResponse({'ok': False, 'error': 'Unknown item type.'}, status=400)

        return JsonResponse({'ok': True})

    # ---------- AJAX: quick upload into current folder ----------

    def explorer_upload(self, request):
        category_id = request.POST.get('category_id')
        category = None
        if category_id and category_id not in ('null', ''):
            category = get_object_or_404(Category, pk=category_id)

        uploaded_files = request.FILES.getlist('files')
        created = []
        rejected = []

        for f in uploaded_files:
            name_no_ext, ext = os.path.splitext(f.name)
            ext_lower = ext.lower()

            if ext_lower in PDF_EXTENSIONS:
                material_type = 'pdf'
            elif ext_lower in IMAGE_EXTENSIONS:
                material_type = 'image'
            else:
                rejected.append(f.name)
                continue

            material = Material(title=name_no_ext, material_type=material_type, category=category)
            material.file.save(f.name, f, save=False)
            material.save()
            created.append(f.name)

        return JsonResponse({'ok': True, 'created': created, 'rejected': rejected})
    
    def explorer_add_vimeo(self, request):

        title = request.POST.get('title', '').strip()
        url = request.POST.get('url', '').strip()
        category_id = request.POST.get('category_id')

        if not title:
            return JsonResponse({'ok': False, 'error': 'Başlık boş olamaz.'}, status=400)
        if not url or 'vimeo.com' not in url:
            return JsonResponse({'ok': False, 'error': 'Geçerli bir Vimeo linki girin.'}, status=400)

        category = None
        if category_id and category_id not in ('null', ''):
            category = get_object_or_404(Category, pk=category_id)

        # Auto-convert a normal share link (vimeo.com/123456789) into the real
        # embeddable player URL (player.vimeo.com/video/123456789) — this is
        # what the iframe in video_viewer.html actually needs, so Bilge can
        # just paste whatever link Vimeo gives her without knowing the
        # difference.
        match = re_module.search(r'vimeo\.com/(?:video/)?(\d+)', url)
        if match:
            video_id = match.group(1)
            embed_url = f'https://player.vimeo.com/video/{video_id}'
        else:
            embed_url = url  # already looks like a player URL or unrecognized format, use as-is

        material = Material(
            title=title,
            material_type='vimeo',
            embed_url=embed_url,
            category=category,
        )
        material.save()

        return JsonResponse({'ok': True, 'id': material.pk})
    
    def explorer_search(self, request):
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

        results = []

        for material in Material.objects.filter(title__icontains=query).select_related('category')[:50]:
            results.append({
                'type': 'material',
                'id': material.pk,
                'name': material.title,
                'material_type': material.material_type,
                'path': breadcrumb_path(material.category),
                'navigate_to': material.category.pk if material.category else '',
            })

        for category in Category.objects.filter(name__icontains=query)[:50]:
            results.append({
                'type': 'category',
                'id': category.pk,
                'name': category.name,
                'path': breadcrumb_path(category.parent),
                'navigate_to': category.pk,
            })

        return JsonResponse({'results': results})
