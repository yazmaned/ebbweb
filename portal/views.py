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
from content.models import Category
from accounts.models import AdminMessage

# Bilge and yazman are the two privileged (admin/superuser teacher) accounts —
# both get full portal access, and both are excluded from every "student" list
# since neither of them is actually a student.
PRIVILEGED_USERNAMES = ('bilge', 'yazman')


def is_bilge(user):
    return user.username in PRIVILEGED_USERNAMES


@login_required
@user_passes_test(is_bilge)
def delete_message(request, pk):
    AdminMessage.objects.filter(pk=pk).delete()
    return redirect('/portal/messages/')


@login_required
@user_passes_test(is_bilge)
def compose_message(request):
    students = User.objects.filter(is_staff=False).exclude(username__in=PRIVILEGED_USERNAMES).order_by('username')
    sent = False

    if request.method == 'POST':
        target = request.POST.get('target')
        text = request.POST.get('message', '').strip()
        if text:
            if target == 'all':
                AdminMessage.objects.create(user=None, message=text)
            else:
                AdminMessage.objects.create(user_id=target, message=text)
            sent = True

    recent_messages = AdminMessage.objects.select_related('user').order_by('-created_at')[:20]

    return render(request, 'portal/compose_message.html', {
        'students': students,
        'sent': sent,
        'recent_messages': recent_messages,
    })


@login_required
@user_passes_test(is_bilge)
def manage_active_course(request):
    active_course = Category.objects.filter(is_active_course=True, parent=None).first()
    root_categories = Category.objects.filter(parent=None).order_by('order', 'name')
    students = User.objects.filter(
        is_staff=False, userprofile__has_library_access=True
    ).exclude(username__in=PRIVILEGED_USERNAMES).order_by('username')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'end_course':
            if active_course:
                active_course.is_active_course = False
                active_course.allowed_users.clear()
                active_course.save()
            return redirect('/portal/active-course/')

        elif action == 'set_course':
            category_id = request.POST.get('category_id')
            selected_user_ids = request.POST.getlist('user_ids')

            Category.objects.filter(is_active_course=True).update(is_active_course=False)

            category = get_object_or_404(Category, pk=category_id, parent=None)
            category.is_active_course = True
            category.save()
            category.allowed_users.set(selected_user_ids)

            return redirect('/portal/active-course/')

    allowed_ids = set(active_course.allowed_users.values_list('pk', flat=True)) if active_course else set()

    return render(request, 'portal/active_course.html', {
        'active_course': active_course,
        'root_categories': root_categories,
        'students': students,
        'allowed_ids': allowed_ids,
    })


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
    students = User.objects.filter(is_staff=False).exclude(username__in=PRIVILEGED_USERNAMES).select_related('userprofile').order_by('username')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ogrenci_listesi.pdf"'

    p = pdf_canvas.Canvas(response, pagesize=landscape(A4))
    width, height = landscape(A4)

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
    active_course = Category.objects.filter(is_active_course=True, parent=None).first()

    if request.method == 'POST':
        username = request.POST.get('username').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        registration_note = request.POST.get('registration_note', '').strip()
        grant_library_access = 'grant_library_access' in request.POST
        grant_active_course = 'grant_active_course' in request.POST

        if User.objects.filter(username=username).exists():
            error = 'Bu kullanıcı adı zaten mevcut.'
        else:
            generated_password = str(random.randint(1000, 9999))
            user = User.objects.create_user(
                username=username,
                password=generated_password,
                first_name=first_name,
                last_name=last_name,
            )

            # Active course visibility requires library access as a prerequisite
            # (checked before the course lookup even runs in the dashboard views) —
            # so a course-only checkbox with no library access would leave the
            # student unable to see anything at all. Force it on together.
            if grant_active_course and active_course:
                grant_library_access = True

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.must_change_password = True
            profile.registration_note = registration_note
            profile.is_self_registered = False
            profile.has_library_access = grant_library_access
            profile.save()

            if grant_active_course and active_course:
                active_course.allowed_users.add(user)

            success = f'"{username}" başarıyla eklendi!'

    return render(request, 'portal/add_student.html', {
        'success': success,
        'error': error,
        'generated_password': generated_password,
        'username': username if success else '',
        'active_course': active_course,
    })

@login_required
@user_passes_test(is_bilge)
def rename_student(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        new_username = request.POST.get('new_username', '').strip()
        new_first_name = request.POST.get('new_first_name', '').strip()
        new_last_name = request.POST.get('new_last_name', '').strip()

        if new_username and not User.objects.exclude(pk=pk).filter(username=new_username).exists():
            user.username = new_username

        user.first_name = new_first_name
        user.last_name = new_last_name
        user.save()

    return redirect('/portal/students/')

@login_required
@user_passes_test(is_bilge)
def student_list(request):
    students = User.objects.filter(is_staff=False).exclude(username__in=PRIVILEGED_USERNAMES).select_related('userprofile').order_by('-date_joined')
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