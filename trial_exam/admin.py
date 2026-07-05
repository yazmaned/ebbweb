from django.contrib import admin
from .models import TrialExamQuestion, TrialExamOption, TrialExamLevel, TrialExamAttempt, TrialExamAnswer


class TrialExamOptionInline(admin.TabularInline):
    model = TrialExamOption
    extra = 0


@admin.register(TrialExamQuestion)
class TrialExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('number', 'section', 'text')
    list_filter = ('section',)
    search_fields = ('text',)
    inlines = [TrialExamOptionInline]


@admin.register(TrialExamLevel)
class TrialExamLevelAdmin(admin.ModelAdmin):
    list_display = ('min_correct', 'max_correct', 'level')


@admin.register(TrialExamAttempt)
class TrialExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'total', 'level', 'completed_at')
    list_filter = ('level',)
    search_fields = ('user__username',)
    readonly_fields = ('user', 'score', 'total', 'level', 'completed_at')
