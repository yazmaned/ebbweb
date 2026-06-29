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
    
from .models import VisitorLog
from user_agents import parse

from django.utils import timezone

class VisitorLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            if not request.user.is_authenticated:
                path = request.path
                skip = ['/static/', '/media/', '/muthisadmin/', '/accounts/messages/', '/sitemap', '/robots']
                if not any(path.startswith(s) for s in skip):
                    ua_string = request.META.get('HTTP_USER_AGENT', '')
                    ua = parse(ua_string)
                    ip = request.META.get('REMOTE_ADDR')

                    # Check if this IP visited today
                    today = timezone.now().date()
                    is_unique = not VisitorLog.objects.filter(
                        ip_address=ip,
                        visited_at__date=today
                    ).exists()

                    VisitorLog.objects.create(
                        ip_address=ip,
                        user_agent=ua_string,
                        browser=f"{ua.browser.family} {ua.browser.version_string}",
                        os=f"{ua.os.family} {ua.os.version_string}",
                        device=ua.device.family,
                        path=path,
                        referer=request.META.get('HTTP_REFERER', ''),
                        is_bot=ua.is_bot,
                        is_unique=is_unique,
                    )
        except Exception:
            pass

        return response