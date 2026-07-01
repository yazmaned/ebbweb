from django.db import models
from django.contrib.auth.models import User

class VocabUnit(models.Model):
    number = models.IntegerField(unique=True)
    title = models.CharField(max_length=200)

    def __str__(self):
        return f"Unit {self.number}: {self.title}"

    class Meta:
        ordering = ['number']

class Word(models.Model):
    unit = models.ForeignKey(VocabUnit, on_delete=models.CASCADE, related_name='words')
    word = models.CharField(max_length=100)
    turkish_meaning = models.CharField(max_length=300)
    collocation = models.CharField(max_length=300, blank=True)
    synonyms = models.JSONField(default=list)

    def __str__(self):
        return self.word

    class Meta:
        ordering = ['id']

class VocabTest(models.Model):
    unit = models.ForeignKey(VocabUnit, on_delete=models.CASCADE, related_name='tests')
    test_id = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    passage = models.TextField(blank=True) ###

    def __str__(self):
        return f"{self.unit} - {self.title}"

class VocabQuestion(models.Model):
    test = models.ForeignKey(VocabTest, on_delete=models.CASCADE, related_name='questions')
    number = models.IntegerField()
    text = models.TextField()

    def __str__(self):
        return f"Q{self.number}: {self.text[:60]}"

    class Meta:
        ordering = ['number']

class VocabOption(models.Model):
    LETTER_CHOICES = [('A','A'),('B','B'),('C','C'),('D','D'),('E','E')]
    question = models.ForeignKey(VocabQuestion, on_delete=models.CASCADE, related_name='options')
    letter = models.CharField(max_length=1, choices=LETTER_CHOICES)
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['letter']

class VocabAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    test = models.ForeignKey(VocabTest, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

class VocabAnswer(models.Model):
    attempt = models.ForeignKey(VocabAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(VocabQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(VocabOption, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)