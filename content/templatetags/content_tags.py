from django import template

register = template.Library()

@register.inclusion_tag('content/folder.html')
def render_folder(category, depth=0):
    return {
        'category': category,
        'children': category.children.all(),
        'materials': category.materials.all(),
        'depth': depth,
        'next_depth': depth + 1,
    }