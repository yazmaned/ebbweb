from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, default='#2c3e50')
    order = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

class Material(models.Model):
    TYPE_CHOICES = [('pdf', 'PDF'), ('video', 'Video (Sunucuda)'), ('youtube', 'YouTube Gömme'), ('vimeo', 'Vimeo Gömme')]
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='materials/', blank=True, null=True)
    embed_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'title']

