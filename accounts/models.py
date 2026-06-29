from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    must_change_password = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
    
class StudentPasswordLog(models.Model):
    username = models.CharField(max_length=150)
    rpassword = models.CharField(max_length=500)
    set_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} - {self.set_at}"

class SessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device = models.CharField(max_length=300, blank=True)
    browser = models.CharField(max_length=300, blank=True)
    os = models.CharField(max_length=300, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    current_material = models.CharField(max_length=300, blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.login_time}"

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    browser = models.CharField(max_length=200, blank=True)
    os = models.CharField(max_length=200, blank=True)
    device = models.CharField(max_length=200, blank=True)
    path = models.CharField(max_length=500, blank=True)
    referer = models.CharField(max_length=500, blank=True)
    visited_at = models.DateTimeField(auto_now_add=True)
    is_bot = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ip_address} - {self.path} - {self.visited_at}"

    class Meta:
        ordering = ['-visited_at']
    
class AdminMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # null = send to all
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        target = self.user.username if self.user else 'Everyone'
        return f"To {target}: {self.message[:50]}"
    
class Journal(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to='journal/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    show_on_home = models.BooleanField(default=True)
    show_timestamp = models.BooleanField(default=True)
    is_seo = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            title = self.title
            title = title.replace('ş', 's').replace('ğ', 'g').replace('ü', 'u')
            title = title.replace('ö', 'o').replace('ı', 'i').replace('ç', 'c')
            title = title.replace('Ş', 'S').replace('Ğ', 'G').replace('Ü', 'U')
            title = title.replace('Ö', 'O').replace('İ', 'I').replace('Ç', 'C')
            self.slug = slugify(title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']