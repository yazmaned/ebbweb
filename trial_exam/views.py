from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import TrialExamQuestion, TrialExamAttempt, TrialExamAnswer, TrialExamLevel
from accounts.models import UserProfile


@login_required
def trial_exam_entry(request):
    """Shows a retry-confirmation screen if the user already has a previous
    attempt, unless they've explicitly confirmed via ?confirmed=1."""
    last_attempt = TrialExamAttempt.objects.filter(user=request.user).order_by('-completed_at').first()

    if last_attempt and request.GET.get('confirmed') != '1':
        return render(request, 'trial_exam/confirm.html', {'last_attempt': last_attempt})

    questions = TrialExamQuestion.objects.all().prefetch_related('options')
    return render(request, 'trial_exam/exam.html', {'questions': questions})


def _find_level_for_score(score):
    level = TrialExamLevel.objects.filter(min_correct__lte=score, max_correct__gte=score).first()
    return level


@login_required
def trial_exam_submit(request):
    if request.method != 'POST':
        return redirect('trial_exam_entry')

    questions = TrialExamQuestion.objects.all().prefetch_related('options')
    total = questions.count()
    score = 0

    attempt = TrialExamAttempt.objects.create(user=request.user, total=total)

    for question in questions:
        selected_letter = request.POST.get(f'q{question.id}')
        selected_option = question.options.filter(letter=selected_letter).first() if selected_letter else None
        is_correct = selected_option.is_correct if selected_option else False
        if is_correct:
            score += 1
        TrialExamAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=selected_option,
            is_correct=is_correct,
        )

    level_obj = _find_level_for_score(score)
    level_name = level_obj.level if level_obj else ''

    attempt.score = score
    attempt.level = level_name
    attempt.save()

    # Update the fields shown on the home page user-status card.
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.latest_trial_score = score
    profile.latest_trial_level = level_name
    profile.save()

    return redirect('trial_exam_result', attempt_id=attempt.id)


@login_required
def trial_exam_result(request, attempt_id):
    attempt = get_object_or_404(TrialExamAttempt, pk=attempt_id)

    if attempt.user != request.user:
        return redirect('home')

    answers = attempt.answers.select_related('question', 'selected_option').prefetch_related('question__options')
    level_obj = TrialExamLevel.objects.filter(min_correct__lte=attempt.score, max_correct__gte=attempt.score).first()

    return render(request, 'trial_exam/result.html', {
        'attempt': attempt,
        'answers': answers,
        'level_feedback': level_obj.feedback_tr if level_obj else '',
    })
