from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import VocabUnit, Word, VocabTest, VocabQuestion, VocabOption, VocabAttempt, VocabAnswer
import random
from io import BytesIO
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Image
import os
from django.conf import settings

FREE_UNIT_LIMIT = 2  # Unit 1 and 2 are free

def vocab_home(request):
    units = VocabUnit.objects.all()
    return render(request, 'vocabulary/home.html', {'units': units})

def flashcards(request):
    unit_id = request.GET.get('unit')
    if unit_id:
        words = list(Word.objects.filter(unit_id=unit_id))
    else:
        words = list(Word.objects.all())
    random.shuffle(words)

    words_json = [
        {'word': w.word, 'turkish': w.turkish_meaning, 'collocation': w.collocation, 'synonyms': w.synonyms}
        for w in words
    ]
    return render(request, 'vocabulary/flashcards.html', {'words': words, 'words_json': words_json})

def vocab_units(request):
    """List of units with lock indicators for free users"""
    units = VocabUnit.objects.all().prefetch_related('tests')
    is_registered = request.user.is_authenticated
    
    unit_data = []
    for unit in units:
        is_locked = not is_registered and unit.number > FREE_UNIT_LIMIT
        unit_data.append({
            'unit': unit,
            'is_locked': is_locked,
            'test_count': unit.tests.count(),
        })
    
    return render(request, 'vocabulary/units.html', {
        'unit_data': unit_data,
        'is_registered': is_registered,
    })

def vocab_unit_tests(request, unit_number):
    """List of tests inside a unit"""
    unit = get_object_or_404(VocabUnit, number=unit_number)
    
    # Block free users from paid units
    if not request.user.is_authenticated and unit.number > FREE_UNIT_LIMIT:
        return redirect('/vocabulary/tests/')
    
    tests = unit.tests.all()
    return render(request, 'vocabulary/unit_tests.html', {'unit': unit, 'tests': tests})

def vocab_quiz(request, test_id):
    """Start a specific test"""
    test = get_object_or_404(VocabTest, pk=test_id)
    
    # Block free users from paid units
    if not request.user.is_authenticated and test.unit.number > FREE_UNIT_LIMIT:
        return redirect('/vocabulary/tests/')
    
    return render(request, 'vocabulary/quiz.html', {'test': test})

def vocab_quiz_submit(request, test_id):
    if request.method != 'POST':
        return redirect('/vocabulary/tests/')
    
    test = get_object_or_404(VocabTest, pk=test_id)
    questions = test.questions.all()
    
    attempt = VocabAttempt.objects.create(
        user=request.user if request.user.is_authenticated else None,
        test=test,
        total=questions.count()
    )
    
    score = 0
    for question in questions:
        selected_letter = request.POST.get(f'q{question.id}')
        selected_option = question.options.filter(letter=selected_letter).first()
        is_correct = selected_option.is_correct if selected_option else False
        if is_correct:
            score += 1
        VocabAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=selected_option,
            is_correct=is_correct
        )
    
    attempt.score = score
    attempt.save()
    request.session['last_vocab_attempt_id'] = attempt.id
    return redirect(f'/vocabulary/result/{attempt.id}/')

def vocab_result(request, attempt_id):
    attempt = get_object_or_404(VocabAttempt, pk=attempt_id)
    
    if attempt.user and request.user != attempt.user:
        return redirect('/home/')
    if not attempt.user:
        if int(request.session.get('last_vocab_attempt_id', 0)) != attempt_id:
            return redirect('/home/')
    
    answers = attempt.answers.select_related('question', 'selected_option').prefetch_related('question__options')
    return render(request, 'vocabulary/result.html', {'attempt': attempt, 'answers': answers})

TR_MAP = str.maketrans({
    'ğ': 'g', 'Ğ': 'G',
    'ş': 's', 'Ş': 'S',
    'ı': 'i', 'İ': 'I',
    'ç': 'c', 'Ç': 'C',
    'ö': 'o', 'Ö': 'O',
    'ü': 'u', 'Ü': 'U',
})

def tr(text):
    if text is None:
        return ''
    return str(text).translate(TR_MAP)

def vocab_result_pdf(request, attempt_id):
    attempt = get_object_or_404(VocabAttempt, pk=attempt_id)

    if attempt.user and request.user != attempt.user:
        return redirect('/home/')
    if not attempt.user:
        if int(request.session.get('last_vocab_attempt_id', 0)) != attempt_id:
            return redirect('/home/')

    answers = attempt.answers.select_related('question', 'selected_option').prefetch_related('question__options')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)

    title_style = ParagraphStyle('TitleCustom', fontName='Helvetica-Bold', fontSize=18, spaceAfter=4)
    sub_style = ParagraphStyle('SubCustom', fontName='Helvetica', fontSize=11, textColor=colors.HexColor('#666666'), spaceAfter=16)
    q_style = ParagraphStyle('QCustom', fontName='Helvetica-Bold', fontSize=10.5, spaceBefore=10, spaceAfter=6)
    skip_style = ParagraphStyle('SkipCustom', fontName='Helvetica-Oblique', fontSize=9.5, leftIndent=14, textColor=colors.HexColor('#999999'), spaceAfter=2)

    story = []
    story.append(Paragraph(tr(f"{attempt.test.unit.title} - {attempt.test.title}"), title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(tr(f"Sonuc: {attempt.score} / {attempt.total} dogru"), sub_style))

    for i, answer in enumerate(answers, start=1):
        story.append(Paragraph(tr(f"{i}. {answer.question.text}"), q_style))

        if not answer.selected_option_id:
            story.append(Paragraph(tr("Bu soru bos birakildi."), skip_style))

        for option in answer.question.options.all():
            label = tr(f"{option.letter.lower()}) {option.text.lower()}")
            if option.is_correct:
                color = colors.HexColor('#16a085')
                label += "  [" + tr("Dogru Cevap") + "]"
            elif answer.selected_option_id == option.id:
                color = colors.HexColor('#e74c3c')
                label += "  [" + tr("Ogrencinin Cevabi") + "]"
            else:
                color = colors.HexColor('#333333')
            opt_style = ParagraphStyle('opt', fontName='Helvetica', fontSize=10, leftIndent=14, spaceAfter=2, textColor=color)
            story.append(Paragraph(label, opt_style))
        story.append(Spacer(1, 4))

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'square_solid.png')
    if os.path.exists(logo_path):
        story.append(Spacer(1, 24))
        logo = Image(logo_path, width=2.2*cm, height=2.2*cm)
        logo.hAlign = 'CENTER'
        story.append(logo)
        story.append(Spacer(1, 6))
        site_style = ParagraphStyle('SiteCustom', fontName='Helvetica', fontSize=10,
                                     textColor=colors.HexColor('#555555'), alignment=1)
        story.append(Paragraph('bilgehanhoca.com', site_style))

    doc.build(story)
    buffer.seek(0)

    filename = tr(f"sonuc_{attempt.test.unit.number}_{attempt.test.title}_{attempt.id}.pdf").replace(' ', '_')
    return FileResponse(buffer, as_attachment=True, filename=filename)