import json
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from vocabulary.models import VocabUnit, VocabTest, VocabQuestion, VocabOption

def run(json_path):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    for unit_data in data['units']:
        unit, _ = VocabUnit.objects.get_or_create(
            number=unit_data['unit'],
            defaults={'title': unit_data['title']}
        )

        for test_data in unit_data['tests']:
            if test_data['type'] != 'reading_comprehension':
                continue

            test, created = VocabTest.objects.get_or_create(
                unit=unit,
                test_id=test_data['id'],
                defaults={'title': test_data['title']}
            )

            if not created:
                print(f"EXIST Unit {unit.number} / {test_data['id']} — already imported, skipping")
                continue

            test.passage = test_data.get('passage', '')
            test.save()

            for q in test_data['questions']:
                question = VocabQuestion.objects.create(
                    test=test,
                    number=q['question_number'],
                    text=q['question']
                )
                correct_letter = q['correct_answer']
                for letter, text in q['options'].items():
                    VocabOption.objects.create(
                        question=question,
                        letter=letter,
                        text=text,
                        is_correct=(letter == correct_letter)
                    )

            print(f"OK    Unit {unit.number} / {test_data['id']} — {len(test_data['questions'])} questions imported")

if __name__ == '__main__':
    run('vocab_questions.json')  # adjust path to wherever your JSON file lives