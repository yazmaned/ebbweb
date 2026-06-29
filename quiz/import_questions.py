import os
import sys
import django
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from quiz.models import Passage, Question, Option

with open('ELSreading_questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    passage, created = Passage.objects.get_or_create(
        title=item['passage_title'],
        defaults={
            'text': item['passage_text'],
            'section': item['section'],
        }
    )
    if created:
        print(f"✅ Created: {passage.title}")
    else:
        print(f"⏭ Skipped (exists): {passage.title}")
        continue

    for q in item['questions']:
        question = Question.objects.create(
            passage=passage,
            number=q['question_number'],
            text=q['question'],
        )
        for letter, text in q['options'].items():
            Option.objects.create(
                question=question,
                letter=letter,
                text=text,
                is_correct=(letter == q['correct_answer'])
            )

print("Done! Imported", Passage.objects.count(), "passages.")