from django.db import models
from django.contrib.auth.models import User

class Passage(models.Model):
    SECTION_CHOICES = [
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
    ]
    title = models.CharField(max_length=300)
    text = models.TextField()
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['section', 'title']

class Question(models.Model):
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE, related_name='questions')
    number = models.IntegerField()
    text = models.TextField()

    def __str__(self):
        return f"{self.passage.title} - Q{self.number}"

    class Meta:
        ordering = ['number']

class Option(models.Model):
    LETTER_CHOICES = [('A','A'),('B','B'),('C','C'),('D','D'),('E','E')]
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    letter = models.CharField(max_length=1, choices=LETTER_CHOICES)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.letter}: {self.text[:50]}"

    class Meta:
        ordering = ['letter']

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user = self.user.username if self.user else 'Anonymous'
        return f"{user} - {self.passage.title} - {self.score}/{self.total}"

class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Q{self.question.number} - {'✓' if self.is_correct else '✗'}"