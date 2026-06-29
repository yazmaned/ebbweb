from django.contrib import admin
from .models import Passage, Question, Option, QuizAttempt, QuizAnswer

class OptionInline(admin.TabularInline):
    model = Option
    extra = 0

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0

@admin.register(Passage)
class PassageAdmin(admin.ModelAdmin):
    list_display = ('title', 'section')
    list_filter = ('section',)
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('passage', 'number', 'text')
    inlines = [OptionInline]

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'passage', 'score', 'total', 'completed_at')
    readonly_fields = ('user', 'passage', 'score', 'total', 'completed_at')

admin.site.register(QuizAnswer)