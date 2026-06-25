from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import SessionLog
from django.db import models
import user_agents
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import AdminMessage, UserProfile, StudentPasswordLog
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import SetNewPasswordForm
from .forms import CustomLoginForm, SetNewPasswordForm

@login_required
def change_password(request):
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            raw = form.cleaned_data['new_password1']
            user.set_password(raw)
            user.save()
            update_session_auth_hash(request, user)
            profile = UserProfile.objects.get(user=request.user)
            profile.must_change_password = False
            profile.save()
            StudentPasswordLog.objects.create(
                username=user.username,
                rpassword=raw,
            )
            
            return redirect('/home/')
    else:
        form = SetNewPasswordForm()
    return render(request, 'accounts/change_password.html', {'form': form})

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            ua_string = request.META.get('HTTP_USER_AGENT', '')
            ua = user_agents.parse(ua_string)

            SessionLog.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            device=ua.device.family,
            browser=f"{ua.browser.family} {ua.browser.version_string}",
            os=f"{ua.os.family} {ua.os.version_string}",
)
            return redirect('/home/')
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    # mark session as inactive
    SessionLog.objects.filter(user=request.user, is_active=True).update(is_active=False)
    logout(request)
    return redirect('/home/')

@login_required
def get_messages(request):
    messages = AdminMessage.objects.filter(
        is_read=False
    ).filter(
        models.Q(user=request.user) | models.Q(user=None)
    ).values('id', 'message', 'created_at')
    return JsonResponse({'messages': list(messages)})

@login_required
def mark_read(request, message_id):
    AdminMessage.objects.filter(id=message_id, user=request.user).update(is_read=True)
    AdminMessage.objects.filter(id=message_id, user=None).update(is_read=True)
    return JsonResponse({'status': 'ok'})