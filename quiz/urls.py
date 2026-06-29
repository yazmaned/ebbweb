from django.urls import path
from . import views

urlpatterns = [
    path('mini/', views.mini_quiz, name='mini_quiz'),
    path('mini/submit/<int:passage_id>/', views.mini_quiz_submit, name='mini_quiz_submit'),
    path('result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('full/', views.full_quiz, name='full_quiz'),
]