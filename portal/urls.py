from django.urls import path
from . import views

urlpatterns = [
    path('add-student/', views.add_student, name='add_student'),
    path('students/', views.student_list, name='student_list'),
    path('students/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('students/export/', views.export_students_pdf, name='export_students_pdf'),
    path('students/toggle-access/<int:pk>/', views.toggle_library_access, name='toggle_library_access'),
    path('students/edit-note/<int:pk>/', views.edit_student_note, name='edit_student_note'),
    path('active-course/', views.manage_active_course, name='manage_active_course'),
    path('messages/', views.compose_message, name='compose_message'),
    path('messages/delete/<int:pk>/', views.delete_message, name='delete_message'),
]