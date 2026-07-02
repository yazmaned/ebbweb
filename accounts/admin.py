from django.contrib import admin
from .models import SessionLog, AdminMessage, StudentPasswordLog, Journal, UserProfile, VisitorLog


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active')
    list_editable = ('is_active',)
    ordering = ('-created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'registration_note', 'latest_trial_score')
    search_fields = ('user__username', 'registration_note')


@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'browser', 'os', 'device', 'login_time', 'current_material', 'last_activity', 'is_active')
    list_filter = ('is_active', 'user')
    search_fields = ('user__username', 'ip_address', 'browser', 'os')
    readonly_fields = ('user', 'ip_address', 'device', 'browser', 'os', 'login_time', 'current_material', 'last_activity', 'is_active')
    ordering = ('-last_activity',)


@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'browser', 'os', 'device', 'path', 'referer', 'is_unique', 'is_bot', 'visited_at')
    list_filter = ('is_bot', 'is_unique', 'browser', 'os')
    readonly_fields = ('ip_address', 'user_agent', 'browser', 'os', 'device', 'path', 'referer', 'is_bot', 'is_unique', 'visited_at')

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(AdminMessage)
class AdminMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'is_read')
    list_filter = ('is_read', 'user')
    search_fields = ('message', 'user__username')
    ordering = ('-created_at',)


@admin.register(StudentPasswordLog)
class StudentPasswordLogAdmin(admin.ModelAdmin):
    list_display = ('username', 'rpassword', 'set_at')
    readonly_fields = ('username', 'rpassword', 'set_at')
    ordering = ('-set_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False