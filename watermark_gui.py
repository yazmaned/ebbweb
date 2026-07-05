#!/usr/bin/env python3
"""
Bulk PDF Watermarker — Tkinter GUI (with drag & drop)

Drag PDF files or whole folders onto the drop zone, or use the buttons to
pick them the normal way. Set your watermark text, click "Apply Watermark"
— every PDF gets overwritten in place with one large centered watermark.

One bad file can't stop the batch — each file is processed independently;
failures are logged and everything else still completes.

Requires:
    pip install reportlab pypdf tkinterdnd2 --break-system-packages
"""

import os
import io
import threading
import queue
import tkinter as tk
from tkinter import filedialog, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD

from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter


# ---------- Watermarking logic ----------

def resolve_font(font_path):
    if font_path:
        if not os.path.isfile(font_path):
            return "Helvetica-Bold", f"Font file not found, falling back to Helvetica-Bold: {font_path}"
        pdfmetrics.registerFont(TTFont("CustomBold", font_path))
        return "CustomBold", None
    return "Helvetica-Bold", None


def make_watermark_page(width, height, text, font_name, font_size):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setFont(font_name, font_size)
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.25))
    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def watermark_pdf(pdf_path, text, font_name, font_size):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        watermark_page = make_watermark_page(width, height, text, font_name, font_size)
        page.merge_page(watermark_page)
        writer.add_page(page)

    temp_path = pdf_path + ".tmp_watermarked"
    with open(temp_path, "wb") as f:
        writer.write(f)
    os.replace(temp_path, pdf_path)


# ---------- GUI ----------

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk PDF Watermarker")
        self.root.geometry("650x600")

        self.pdf_paths = []
        self.log_queue = queue.Queue()
        self.running = False

        self._build_ui()
        self._poll_log_queue()

    def _build_ui(self):
        pad = {'padx': 10, 'pady': 6}

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill='x', **pad)

        tk.Button(top_frame, text="Select Folder (includes subfolders)", command=self.pick_folder).pack(side='left', padx=4)
        tk.Button(top_frame, text="Select Files", command=self.pick_files).pack(side='left', padx=4)
        tk.Button(top_frame, text="Clear List", command=self.clear_list).pack(side='left', padx=4)

        # --- Drop zone ---
        self.drop_zone = tk.Label(
            self.root,
            text="Drag & drop PDF files or folders here",
            bg="#eef6ff",
            fg="#2c5aa0",
            relief="ridge",
            bd=2,
            height=3,
        )
        self.drop_zone.pack(fill='x', padx=10, pady=(0, 6))
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self.on_drop)

        list_frame = tk.Frame(self.root)
        list_frame.pack(fill='both', expand=False, padx=10, pady=6)

        tk.Label(list_frame, text="Files to watermark:").pack(anchor='w')
        self.listbox = tk.Listbox(list_frame, height=8)
        self.listbox.pack(fill='both', expand=True)
        # Also accept drops directly onto the list itself
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)

        options_frame = tk.Frame(self.root)
        options_frame.pack(fill='x', **pad)

        tk.Label(options_frame, text="Watermark text:").grid(row=0, column=0, sticky='w')
        self.text_entry = tk.Entry(options_frame, width=40)
        self.text_entry.insert(0, "bilgehanhoca.com")
        self.text_entry.grid(row=0, column=1, sticky='w', padx=6)

        tk.Label(options_frame, text="Font size:").grid(row=1, column=0, sticky='w')
        self.size_entry = tk.Entry(options_frame, width=10)
        self.size_entry.insert(0, "80")
        self.size_entry.grid(row=1, column=1, sticky='w', padx=6)

        tk.Label(options_frame, text="Font file (optional, .ttf):").grid(row=2, column=0, sticky='w')
        self.font_path_var = tk.StringVar()
        tk.Entry(options_frame, textvariable=self.font_path_var, width=40).grid(row=2, column=1, sticky='w', padx=6)
        tk.Button(options_frame, text="Browse...", command=self.pick_font).grid(row=2, column=2, padx=4)

        action_frame = tk.Frame(self.root)
        action_frame.pack(fill='x', **pad)

        self.run_button = tk.Button(action_frame, text="Apply Watermark", bg="#28a745", fg="white",
                                     command=self.start_watermarking)
        self.run_button.pack(side='left')

        self.progress = ttk.Progressbar(action_frame, length=300, mode='determinate')
        self.progress.pack(side='left', padx=10)

        self.status_label = tk.Label(self.root, text="Ready.", anchor='w')
        self.status_label.pack(fill='x', **pad)

        log_frame = tk.Frame(self.root)
        log_frame.pack(fill='both', expand=True, **pad)
        tk.Label(log_frame, text="Log:").pack(anchor='w')

        log_scroll = tk.Scrollbar(log_frame)
        log_scroll.pack(side='right', fill='y')
        self.log_text = tk.Text(log_frame, height=10, yscrollcommand=log_scroll.set, state='disabled')
        self.log_text.pack(fill='both', expand=True)
        log_scroll.config(command=self.log_text.yview)

    # ---------- Drag & drop ----------

    def on_drop(self, event):
        # event.data is a Tcl-formatted list — paths with spaces are wrapped
        # in {curly braces}. root.tk.splitlist() is the correct way to parse
        # this, rather than a naive .split(' ').
        raw_paths = self.root.tk.splitlist(event.data)

        found_pdfs = []
        for raw_path in raw_paths:
            if os.path.isdir(raw_path):
                for dirpath, _dirnames, filenames in os.walk(raw_path):
                    for fname in filenames:
                        if fname.lower().endswith('.pdf'):
                            found_pdfs.append(os.path.join(dirpath, fname))
            elif os.path.isfile(raw_path) and raw_path.lower().endswith('.pdf'):
                found_pdfs.append(raw_path)

        if not found_pdfs:
            self._log("Dropped item(s) contained no PDF files.")
            return

        self.pdf_paths.extend(found_pdfs)
        self._refresh_listbox()

    # ---------- File selection (buttons) ----------

    def pick_folder(self):
        folder = filedialog.askdirectory(title="Select the folder containing your PDFs")
        if not folder:
            return
        found = []
        for dirpath, _dirnames, filenames in os.walk(folder):
            for fname in filenames:
                if fname.lower().endswith('.pdf'):
                    found.append(os.path.join(dirpath, fname))
        self.pdf_paths.extend(found)
        self._refresh_listbox()

    def pick_files(self):
        files = filedialog.askopenfilenames(title="Select PDF files", filetypes=[("PDF files", "*.pdf")])
        if not files:
            return
        self.pdf_paths.extend(files)
        self._refresh_listbox()

    def pick_font(self):
        font_file = filedialog.askopenfilename(title="Select font file", filetypes=[("TrueType Font", "*.ttf")])
        if font_file:
            self.font_path_var.set(font_file)

    def clear_list(self):
        self.pdf_paths = []
        self._refresh_listbox()

    def _refresh_listbox(self):
        seen = set()
        deduped = []
        for p in self.pdf_paths:
            if p not in seen:
                seen.add(p)
                deduped.append(p)
        self.pdf_paths = deduped

        self.listbox.delete(0, tk.END)
        for p in self.pdf_paths:
            self.listbox.insert(tk.END, p)
        self.status_label.config(text=f"{len(self.pdf_paths)} file(s) listed.")

    # ---------- Watermarking (runs on a background thread) ----------

    def start_watermarking(self):
        if self.running:
            return
        if not self.pdf_paths:
            self._log("Select or drop at least one PDF file first.")
            return

        text = self.text_entry.get().strip()
        if not text:
            self._log("Watermark text cannot be empty.")
            return

        try:
            font_size = int(self.size_entry.get().strip())
        except ValueError:
            self._log("Font size must be a valid number.")
            return

        font_path = self.font_path_var.get().strip() or None

        self.running = True
        self.run_button.config(state='disabled')
        self.progress['value'] = 0
        self.progress['maximum'] = len(self.pdf_paths)
        self._log(f"\n=== Starting: {len(self.pdf_paths)} file(s) ===")

        thread = threading.Thread(
            target=self._watermark_worker,
            args=(list(self.pdf_paths), text, font_path, font_size),
            daemon=True,
        )
        thread.start()

    def _watermark_worker(self, paths, text, font_path, font_size):
        font_name, font_warning = resolve_font(font_path)
        if font_warning:
            self.log_queue.put(('log', font_warning))

        success_count = 0
        error_count = 0

        for i, path in enumerate(paths, start=1):
            try:
                watermark_pdf(path, text, font_name, font_size)
                self.log_queue.put(('log', f"[OK] {path}"))
                success_count += 1
            except Exception as e:
                self.log_queue.put(('log', f"[ERROR] {path} -> {e}"))
                error_count += 1

            self.log_queue.put(('progress', i))

        self.log_queue.put(('log', f"\n=== Done: {success_count} succeeded, {error_count} failed ==="))
        self.log_queue.put(('done', None))

    # ---------- Thread-safe UI updates ----------
    # Tkinter is not thread-safe. The worker thread never touches widgets
    # directly — it only pushes messages onto log_queue, and this poller
    # (running on the main thread via root.after) drains it.

    def _poll_log_queue(self):
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == 'log':
                    self._log(payload)
                elif kind == 'progress':
                    self.progress['value'] = payload
                    self.status_label.config(text=f"Processing... {payload}/{len(self.pdf_paths)}")
                elif kind == 'done':
                    self.running = False
                    self.run_button.config(state='normal')
                    self.status_label.config(text="Done.")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log_queue)

    def _log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = WatermarkApp(root)
    root.mainloop()
