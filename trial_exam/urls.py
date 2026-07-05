from django.urls import path
from . import views

urlpatterns = [
    path('', views.trial_exam_entry, name='trial_exam_entry'),
    path('submit/', views.trial_exam_submit, name='trial_exam_submit'),
    path('result/<int:attempt_id>/', views.trial_exam_result, name='trial_exam_result'),
]
