"""
One-time import of the trial exam JSON into the database.

USAGE:
    python trial_exam/import_exam.py /path/to/yds_yokdil_trial_exam.json

Safe to re-run — questions are matched by `number` and skipped if they
already exist, so running this twice never creates duplicates.
"""

import json
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from trial_exam.models import TrialExamQuestion, TrialExamOption, TrialExamLevel


def run(json_path):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    # --- Scoring levels ---
    level_count = 0
    for tier in data['scoring_table']:
        level, created = TrialExamLevel.objects.get_or_create(
            min_correct=tier['min_correct'],
            max_correct=tier['max_correct'],
            defaults={'level': tier['level'], 'feedback_tr': tier['feedback_tr']},
        )
        if created:
            level_count += 1

    print(f"Scoring levels imported: {level_count}")

    # --- Questions + options ---
    question_count = 0
    skipped_count = 0

    for q in data['questions']:
        if TrialExamQuestion.objects.filter(number=q['number']).exists():
            skipped_count += 1
            continue

        question = TrialExamQuestion.objects.create(
            number=q['number'],
            section=q['section'],
            text=q['question'],
        )

        correct_letter = q['correct_answer']
        for letter, text in q['options'].items():
            TrialExamOption.objects.create(
                question=question,
                letter=letter,
                text=text,
                is_correct=(letter == correct_letter),
            )

        question_count += 1

    print(f"Questions imported: {question_count}")
    print(f"Questions skipped (already existed): {skipped_count}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python trial_exam/import_exam.py /path/to/exam.json")
        sys.exit(1)
    run(sys.argv[1])
