from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import UserProfile
import random
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
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


def truncate_text(text, font, size, max_width):
    if stringWidth(text, font, size) <= max_width:
        return text
    while text and stringWidth(text + '...', font, size) > max_width:
        text = text[:-1]
    return text + '...' if text else '...'


COLUMNS = [
    ('Username', 40, 100),
    ('Date', 140, 70),
    ('Type', 210, 60),
    ('Library', 270, 50),
    ('Phone', 320, 90),
    ('Email', 410, 180),
    ('Note', 590, 172),
]


def draw_table_header(p, y, width):
    p.setFillColor(colors.HexColor('#671789'))
    p.rect(40, y - 4, width - 80, 20, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 9)
    for label, x, _ in COLUMNS:
        p.drawString(x, y, tr(label))


@login_required
@user_passes_test(is_bilge)
def export_students_pdf(request):
    students = User.objects.filter(is_staff=False).exclude(username='bilge').select_related('userprofile').order_by('username')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ogrenci_listesi.pdf"'

    p = pdf_canvas.Canvas(response, pagesize=landscape(A4))
    width, height = landscape(A4)

    # title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 45, tr("Student (User) List"))

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(40, height - 62, tr(f"{datetime.datetime.now().strftime('%d %b %Y %H:%M')}, {students.count()} students."))

    header_y = height - 95
    draw_table_header(p, header_y, width)

    p.setFont("Helvetica", 8)
    y = header_y - 22

    for i, student in enumerate(students):
        if y < 50:
            p.showPage()
            p.setFont("Helvetica-Bold", 16)
            p.setFillColor(colors.black)
            p.drawString(40, height - 45, tr("Student (User) List (devam)"))
            header_y = height - 95
            draw_table_header(p, header_y, width)
            p.setFont("Helvetica", 8)
            y = header_y - 22

        bg = colors.whitesmoke if i % 2 == 0 else colors.white
        p.setFillColor(bg)
        p.rect(40, y - 5, width - 80, 18, fill=1, stroke=0)
        p.setFillColor(colors.black)

        profile = getattr(student, 'userprofile', None)

        reg_type = 'Self' if (profile and profile.is_self_registered) else 'Manual'
        library_status = 'Yes' if (profile and profile.has_library_access) else 'No'
        phone = profile.phone_number if (profile and profile.phone_number) else '-'
        email = student.email if student.email else '-'
        note = profile.registration_note if (profile and profile.registration_note) else '-'

        row_values = [
            tr(student.username),
            student.date_joined.strftime('%d %b %Y'),
            reg_type,
            library_status,
            tr(phone),
            tr(email),
            tr(note),
        ]

        for (label, x, col_width), value in zip(COLUMNS, row_values):
            display_value = truncate_text(value, "Helvetica", 8, col_width - 6)
            p.drawString(x, y, display_value)

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
        registration_note = request.POST.get('registration_note', '').strip()

        if User.objects.filter(username=username).exists():
            error = 'Bu kullanıcı adı zaten mevcut.'
        else:
            generated_password = str(random.randint(1000, 9999))
            user = User.objects.create_user(
                username=username,
                password=generated_password,
            )
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.must_change_password = True
            profile.registration_note = registration_note
            profile.is_self_registered = False
            profile.has_library_access = True
            profile.save()
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
    students = User.objects.filter(is_staff=False).exclude(username='bilge').select_related('userprofile').order_by('-date_joined')
    return render(request, 'portal/student_list.html', {'students': students})

@login_required
@user_passes_test(is_bilge)
def edit_student_note(request, pk):
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, user__pk=pk)
        profile.registration_note = request.POST.get('note', '').strip()
        profile.save()
    return redirect('/portal/students/')


@login_required
@user_passes_test(is_bilge)
def delete_student(request, pk):
    user = User.objects.get(pk=pk)
    user.delete()
    return redirect('/portal/students/')


@login_required
@user_passes_test(is_bilge)
def toggle_library_access(request, pk):
    profile = get_object_or_404(UserProfile, user__pk=pk)
    profile.has_library_access = not profile.has_library_access
    profile.save()
    return redirect('/portal/students/')