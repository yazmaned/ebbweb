from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import UserProfile
import random
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib import colors
import datetime


def is_bilge(user):
    return user.username == 'bilge'

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


@login_required
@user_passes_test(is_bilge)
def export_students_pdf(request):
    students = User.objects.filter(is_staff=False).order_by('username')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ogrenci_listesi.pdf"'

    p = pdf_canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, tr("Ogrenci Listesi"))

    # date
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(50, height - 70, tr(f"{datetime.datetime.now().strftime('%d %b %Y %H:%M')} tarihi itibariyle {students.count()} ogrenci."))

    # header
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, height - 110, tr("Kullanici Adi"))
    p.drawString(250, height - 110, tr("Kayit Tarihi"))
    p.line(50, height - 115, width - 50, height - 115)

    # rows
    p.setFont("Helvetica", 10)
    y = height - 135
    for i, student in enumerate(students):
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 50
        bg = colors.whitesmoke if i % 2 == 0 else colors.white
        p.setFillColor(bg)
        p.rect(50, y - 5, width - 100, 18, fill=1, stroke=0)
        p.setFillColor(colors.black)
        p.drawString(55, y, tr(student.username))
        p.drawString(255, y, student.date_joined.strftime('%d %b %Y'))
        y -= 20

    p.save()
    return response


def add_student(request):
    success = None
    error = None
    generated_password = None
    username = ''

    if request.method == 'POST':
        username = request.POST.get('username').strip()

        if User.objects.filter(username=username).exists():
            error = 'Bu kullanıcı adı zaten mevcut.'
        else:
            generated_password = str(random.randint(1000, 9999))
            user = User.objects.create_user(
                username=username,
                password=generated_password,
            )
            UserProfile.objects.get_or_create(user=user, defaults={'must_change_password': True})
            success = f'"{username}" başarıyla eklendi!'

    return render(request, 'portal/add_student.html', {
        'success': success,
        'error': error,
        'generated_password': generated_password,
        'username': username if success else '',
    })


@login_required
@user_passes_test(is_bilge)
def student_list(request):
    students = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'portal/student_list.html', {'students': students})


@login_required
@user_passes_test(is_bilge)
def delete_student(request, pk):
    user = User.objects.get(pk=pk)
    user.delete()
    return redirect('/portal/students/')