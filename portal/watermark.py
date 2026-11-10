import io
import os
import zipfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import render

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

PRIVILEGED_USERNAMES = ('bilge', 'yazman')

# Türkçe karakter (ı, ş, ğ) gerekirse buraya bir .ttf koy; yoksa Helvetica-Bold kullanılır.
FONT_PATH = settings.BASE_DIR / 'static' / 'fonts' / 'watermark.ttf'
_font_name = None


def _get_font():
    global _font_name
    if _font_name is None:
        _font_name = 'Helvetica-Bold'
        if FONT_PATH.is_file():
            try:
                pdfmetrics.registerFont(TTFont('WatermarkFont', str(FONT_PATH)))
                _font_name = 'WatermarkFont'
            except Exception:
                pass
    return _font_name


def _make_watermark_page(width, height, text, font_name, font_size):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setFont(font_name, font_size)
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.25))
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def watermark_bytes(data, text, font_size):
    font_name = _get_font()
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted and not reader.decrypt(''):
        raise ValueError('şifreli PDF, açılamadı')

    # pypdf 7+: sayfalar writer'a ait olmalı, o yüzden önce tüm belgeyi kopyala
    writer = PdfWriter(clone_from=reader)

    cache = {}
    for page in writer.pages:
        box = page.mediabox
        w, h = float(box.width), float(box.height)
        key = (round(w, 1), round(h, 1))
        if key not in cache:
            cache[key] = _make_watermark_page(w, h, text, font_name, font_size)
        page.merge_transformed_page(
            cache[key],
            Transformation().translate(float(box.left), float(box.bottom)),
        )

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@login_required
def watermark_tool(request):
    if request.user.username not in PRIVILEGED_USERNAMES:
        return HttpResponseForbidden()

    ctx = {'text': 'bilgehanhoca.com', 'font_size': 80, 'errors': []}

    if request.method == 'POST':
        files = request.FILES.getlist('files')
        text = request.POST.get('text', '').strip()
        try:
            font_size = int(request.POST.get('font_size', '80'))
        except ValueError:
            font_size = 0
        ctx['text'] = text
        ctx['font_size'] = font_size or 80

        if not files:
            ctx['errors'] = ['En az bir PDF seçin.']
        elif not text:
            ctx['errors'] = ['Filigran metni boş olamaz.']
        elif not 10 <= font_size <= 300:
            ctx['errors'] = ['Yazı boyutu 10 ile 300 arasında olmalı.']
        else:
            results, errors = [], []
            for f in files:
                name = os.path.basename(f.name)
                if not name.lower().endswith('.pdf'):
                    errors.append(f'{name}: PDF değil')
                    continue
                try:
                    results.append((name, watermark_bytes(f.read(), text, font_size)))
                except Exception as e:
                    errors.append(f'{name}: {e}')

            if not results:
                ctx['errors'] = errors or ['Hiçbir dosya işlenemedi.']
            elif len(results) == 1 and not errors:
                name, data = results[0]
                return FileResponse(io.BytesIO(data), as_attachment=True,
                                    filename=name, content_type='application/pdf')
            else:
                zbuf = io.BytesIO()
                used = set()
                with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as z:
                    for name, data in results:
                        base, ext = os.path.splitext(name)
                        final, n = name, 2
                        while final in used:
                            final = f'{base} ({n}){ext}'
                            n += 1
                        used.add(final)
                        z.writestr(final, data)
                    if errors:
                        z.writestr('HATALAR.txt', '\n'.join(errors))
                zbuf.seek(0)
                return FileResponse(zbuf, as_attachment=True,
                                    filename='filigranli_pdfler.zip',
                                    content_type='application/zip')

    return render(request, 'portal/watermark.html', ctx)