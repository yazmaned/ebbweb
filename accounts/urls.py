from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('change-password/', views.change_password, name='change_password'),
    path('messages/', views.get_messages, name='get_messages'),
    path('messages/read/<int:message_id>/', views.mark_read, name='mark_read'),
    path('check-username/', views.check_username_available, name='check_username_available'),

]