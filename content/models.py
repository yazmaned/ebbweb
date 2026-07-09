from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, default='#2c3e50')
    order = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    # --- Active-course feature: a single root-level folder can be flagged as
    # the current course, visible only to the students Bilge picks. When she
    # ends it, is_active_course flips back to False and it becomes a normal
    # folder visible to everyone — no data migration needed for that part.
    is_active_course = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField(User, blank=True, related_name='visible_active_courses')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

class CarouselItem(models.Model):
    image = models.ImageField(upload_to='carousel/')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']

class Material(models.Model):
    TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('video', 'Video (Sunucuda)'),
        ('youtube', 'YouTube Gömme'),
        ('vimeo', 'Vimeo Gömme'),
        ('image', 'Görsel (PNG/JPEG)'),
    ]
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='materials/', blank=True, null=True)
    embed_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.material_type == 'image' and self.file:
            ext = self.file.name.lower().rsplit('.', 1)[-1]
            if ext not in ('png', 'jpg', 'jpeg'):
                raise ValidationError('Sadece PNG veya JPEG dosyaları desteklenir.')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'title']