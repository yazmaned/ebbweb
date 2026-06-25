from django.urls import path
from . import views

urlpatterns = [
    path('add-student/', views.add_student, name='add_student'),
    path('students/', views.student_list, name='student_list'),
    path('students/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('students/export/', views.export_students_pdf, name='export_students_pdf'),
]