from django.db import models
from django.contrib.auth.models import User


class TrialExamQuestion(models.Model):
    number = models.IntegerField(unique=True)
    section = models.CharField(max_length=200)
    text = models.TextField()

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Q{self.number}: {self.text[:60]}"


class TrialExamOption(models.Model):
    LETTER_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')]
    question = models.ForeignKey(TrialExamQuestion, on_delete=models.CASCADE, related_name='options')
    letter = models.CharField(max_length=1, choices=LETTER_CHOICES)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['letter']


class TrialExamLevel(models.Model):
    """One row per scoring tier (e.g. 1-25 correct -> A2/pre-B1)."""
    min_correct = models.IntegerField()
    max_correct = models.IntegerField()
    level = models.CharField(max_length=100)
    feedback_tr = models.TextField()

    class Meta:
        ordering = ['min_correct']

    def __str__(self):
        return f"{self.min_correct}-{self.max_correct}: {self.level}"


class TrialExamAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trial_exam_attempts')
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    level = models.CharField(max_length=100, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.score}/{self.total} ({self.completed_at:%d.%m.%Y})"


class TrialExamAnswer(models.Model):
    attempt = models.ForeignKey(TrialExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(TrialExamQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(TrialExamOption, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
