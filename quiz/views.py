from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Passage, Question, Option, QuizAttempt, QuizAnswer
import random

def mini_quiz(request):
    # Random passage for free mini quiz - no login required
    passage = Passage.objects.order_by('?').first()
    return render(request, 'quiz/mini_quiz.html', {'passage': passage})

def mini_quiz_submit(request, passage_id):
    if request.method != 'POST':
        return redirect('/quiz/mini/')
    
    passage = get_object_or_404(Passage, pk=passage_id)
    questions = passage.questions.all()
    
    attempt = QuizAttempt.objects.create(
        user=request.user if request.user.is_authenticated else None,
        passage=passage,
        total=questions.count()
    )

    score = 0
    for question in questions:
        selected_letter = request.POST.get(f'q{question.id}')
        selected_option = question.options.filter(letter=selected_letter).first()
        is_correct = selected_option.is_correct if selected_option else False
        if is_correct:
            score += 1
        QuizAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=selected_option,
            is_correct=is_correct
        )

    attempt.score = score
    attempt.save()
    request.session['last_attempt_id'] = attempt.id
    return redirect(f'/quiz/result/{attempt.id}/')


def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id)
    
    if attempt.user and request.user != attempt.user:
        return redirect('/home/')
    
    if not attempt.user:
        if int(request.session.get('last_attempt_id', 0)) != attempt_id:
            return redirect('/home/')
    
    answers = attempt.answers.select_related('question', 'selected_option').prefetch_related('question__options')
    return render(request, 'quiz/result.html', {'attempt': attempt, 'answers': answers})

@login_required
def full_quiz(request):
    section = request.GET.get('section', 'INTERMEDIATE')
    passages = Passage.objects.filter(section=section).order_by('?')[:5]
    return render(request, 'quiz/full_quiz.html', {'passages': passages, 'section': section})