from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('file/<int:pk>/', views.serve_file, name='serve_file'),
    path('view/<int:pk>/', views.view_pdf, name='view_pdf'),
    path('video/<int:pk>/', views.view_video, name='view_video'),
    path('home/', views.home, name='home'),
    path('journal/add/', views.add_journal, name='add_journal'),
    path('journal/delete/<int:pk>/', views.delete_journal, name='delete_journal'),
    path('journal/<slug:slug>/', views.view_journal, name='view_journal'),
    path('journal/', views.journal_archive, name='journal_archive'),
    path('about/', views.about, name='about'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('screen/', views.screen, name='screen'),


]