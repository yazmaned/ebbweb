from django.urls import path
from . import views

urlpatterns = [
    path('', views.vocab_home, name='vocab_home'),
    path('flashcards/', views.flashcards, name='flashcards'),
    path('tests/', views.vocab_units, name='vocab_units'),
    path('tests/unit/<int:unit_number>/', views.vocab_unit_tests, name='vocab_unit_tests'),
    path('quiz/<int:test_id>/', views.vocab_quiz, name='vocab_quiz'),
    path('quiz/submit/<int:test_id>/', views.vocab_quiz_submit, name='vocab_quiz_submit'),
    path('result/<int:attempt_id>/', views.vocab_result, name='vocab_result'),
    path('result/<int:attempt_id>/pdf/', views.vocab_result_pdf, name='vocab_result_pdf'),
]