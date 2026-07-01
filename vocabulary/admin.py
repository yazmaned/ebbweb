from django.contrib import admin
from .models import VocabUnit, Word, VocabTest, VocabQuestion, VocabOption, VocabAttempt

class WordInline(admin.TabularInline):
    model = Word
    extra = 0

@admin.register(VocabUnit)
class VocabUnitAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    inlines = [WordInline]

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'turkish_meaning', 'unit', 'collocation')
    list_filter = ('unit',)
    search_fields = ('word', 'turkish_meaning')

class VocabOptionInline(admin.TabularInline):
    model = VocabOption
    extra = 0

@admin.register(VocabQuestion)
class VocabQuestionAdmin(admin.ModelAdmin):
    list_display = ('number', 'test', 'text')
    inlines = [VocabOptionInline]

@admin.register(VocabTest)
class VocabTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit')
    list_filter = ('unit',)

@admin.register(VocabAttempt)
class VocabAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'total', 'completed_at')