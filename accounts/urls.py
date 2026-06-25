from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('messages/', views.get_messages, name='get_messages'),
    path('messages/read/<int:message_id>/', views.mark_read, name='mark_read'),
]