import os
import sys
import django
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from vocabulary.models import VocabUnit, Word, VocabTest, VocabQuestion, VocabOption

# Import vocabulary
with open('vocabulary.json', 'r', encoding='utf-8') as f:
    vocab_data = json.load(f)

for unit_data in vocab_data['units']:
    unit, _ = VocabUnit.objects.get_or_create(
        number=unit_data['unit'],
        defaults={'title': unit_data['title']}
    )
    for w in unit_data['words']:
        Word.objects.get_or_create(
            unit=unit,
            word=w['word'],
            defaults={
                'turkish_meaning': w['turkish_meaning'],
                'collocation': w.get('collocation', ''),
                'synonyms': w.get('synonyms', []),
            }
        )
    print(f"✅ Unit {unit.number}: {len(unit_data['words'])} words")

# Import questions (only fill_in_the_blank type)
with open('vocab_questions.json', 'r', encoding='utf-8') as f:
    q_data = json.load(f)

for unit_data in q_data['units']:
    unit = VocabUnit.objects.get(number=unit_data['unit'])
    for test_data in unit_data['tests']:
        if test_data['type'] != 'fill_in_the_blank':
            continue
        test, created = VocabTest.objects.get_or_create(
            unit=unit,
            test_id=test_data['id'],
            defaults={'title': test_data['title']}
        )
        if not created:
            continue
        for q in test_data['questions']:
            question = VocabQuestion.objects.create(
                test=test,
                number=q['question_number'],
                text=q['question'],
            )
            for letter, text in q['options'].items():
                VocabOption.objects.create(
                    question=question,
                    letter=letter,
                    text=text,
                    is_correct=(letter == q['correct_answer'])
                )
        print(f"  ✅ {test.title}: {len(test_data['questions'])} questions")

print(f"\nDone!")
print(f"Total words: {Word.objects.count()}")
print(f"Total tests: {VocabTest.objects.count()}")
print(f"Total questions: {VocabQuestion.objects.count()}")