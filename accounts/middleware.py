from django.shortcuts import redirect
from .models import UserProfile

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.must_change_password:
                    allowed = ['/accounts/change-password/', '/accounts/logout/']
                    if request.path not in allowed:
                        return redirect('/accounts/change-password/')
            except UserProfile.DoesNotExist:
                pass
        return self.get_response(request)