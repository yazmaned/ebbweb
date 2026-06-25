from django.contrib import admin
from .models import Material, Category

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