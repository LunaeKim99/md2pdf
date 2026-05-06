# app.py
import tkinter as tk
from tkinter import ttk, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import queue
import os
import sys
import subprocess
import re
from converter import convert_md_to_pdf, convert_md_to_docx

VERSION = "v1.2.0"

def open_file(path):
    """Open a file with the default system viewer."""
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.call(['open', path])
    else:
        subprocess.call(['xdg-open', path])


class MarkdownConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"MD to PDF / DOCX Converter {VERSION}")
        self.root.minsize(750, 620)
        self.root.configure(bg='#F7F9FC')

        self.files = []
        self.log_queue = queue.Queue()
        self.is_converting = False

        self._setup_styles()
        self._setup_ui()
        self._poll_log_queue()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TFrame', background='#F7F9FC')
        style.configure('TLabel', background='#F7F9FC', font=('Segoe UI', 10))
        style.configure('Header.TLabel', background='#F7F9FC', font=('Segoe UI', 16, 'bold'), foreground='#2E86AB')
        style.configure('Subtitle.TLabel', background='#F7F9FC', font=('Segoe UI', 10), foreground='#666666')
        style.configure('Hint.TLabel', background='#F7F9FC', font=('Segoe UI', 9, 'italic'), foreground='#999999')
        style.configure('Count.TLabel', background='#F7F9FC', font=('Segoe UI', 9), foreground='#666666')

        style.configure('Input.TLabelframe', background='#F7F9FC')
        style.configure('Input.TLabelframe.Label', background='#F7F9FC', font=('Segoe UI', 10, 'bold'), foreground='#2E86AB')

        style.configure('Convert.TButton', background='#2E86AB', foreground='white', font=('Segoe UI', 12, 'bold'))
        style.map('Convert.TButton',
                  background=[('active', '#1A6A8C'), ('pressed', '#1A6A8C')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        style.configure('Accent.Horizontal.TProgressbar',
                        troughcolor='#E0E0E0',
                        background='#2E86AB',
                        thickness=20)

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill='both', expand=True)

        for i in range(6):
            main_frame.grid_rowconfigure(i, weight=0)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self._build_header(main_frame, 0)
        self._build_input_section(main_frame, 1)
        self._build_output_section(main_frame, 3)
        self._build_options_section(main_frame, 4)
        self._build_convert_section(main_frame, 5)
        self._build_log_section(main_frame, 6)

    def _build_header(self, parent, row):
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=row, column=0, sticky='ew', pady=(0, 10))

        ttk.Label(header_frame, text=f"\U0001F4C4 MD \u2192 PDF / DOCX Converter {VERSION}",
                  style='Header.TLabel').pack(anchor='w')
        ttk.Label(header_frame, text="Convert Markdown to styled PDF or DOCX",
                  style='Subtitle.TLabel').pack(anchor='w')

    def _build_input_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="INPUT FILES", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='nsew', pady=5)

        list_frame = ttk.Frame(lf)
        list_frame.pack(fill='both', expand=True, padx=10, pady=(10, 5))

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            height=6,
            bg='#FFFFFF',
            selectbackground='#2E86AB',
            selectforeground='white',
            font=('Segoe UI', 10),
            borderwidth=1,
            relief='solid'
        )
        self.listbox.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)

        hint_frame = ttk.Frame(lf)
        hint_frame.pack(fill='x', padx=10, pady=(0, 5))

        self.hint_label = ttk.Label(hint_frame, text="\U0001F4A1 Drag & drop .md files here", style='Hint.TLabel')
        self.hint_label.pack(side='left')

        self.count_label = ttk.Label(hint_frame, text="[File count: 0]", style='Count.TLabel')
        self.count_label.pack(side='right')

        btn_frame = ttk.Frame(lf)
        btn_frame.pack(fill='x', padx=10, pady=(0, 10))

        ttk.Button(btn_frame, text="Add Files", command=self.add_files).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side='left', padx=(5, 0))

    def _build_output_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="OUTPUT FOLDER", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='ew', pady=5)

        output_frame = ttk.Frame(lf)
        output_frame.pack(fill='x', padx=10, pady=10)

        self.output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_var, font=('Segoe UI', 10)).pack(
            side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side='left')

    def _build_options_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="OPTIONS", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='ew', pady=5)

        opts_frame = ttk.Frame(lf)
        opts_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(opts_frame, text="Theme:", font=('Segoe UI', 10)).pack(side='left', padx=(0, 5))
        self.theme_var = tk.StringVar(value="Default")
        theme_combo = ttk.Combobox(
            opts_frame,
            textvariable=self.theme_var,
            values=["Default", "Dark", "Academic", "Minimal"],
            state="readonly",
            width=14,
            font=('Segoe UI', 10)
        )
        theme_combo.pack(side='left', padx=(0, 15))

        ttk.Label(opts_frame, text="Format:", font=('Segoe UI', 10)).pack(side='left', padx=(0, 5))
        self.format_var = tk.StringVar(value="PDF")
        format_combo = ttk.Combobox(
            opts_frame,
            textvariable=self.format_var,
            values=["PDF", "DOCX", "Both"],
            state="readonly",
            width=10,
            font=('Segoe UI', 10)
        )
        format_combo.pack(side='left', padx=(0, 20))

        self.open_file_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts_frame,
            text="Open file after conversion",
            variable=self.open_file_var,
            font=('Segoe UI', 10)
        ).pack(side='left')

    def _build_convert_section(self, parent, row):
        convert_frame = ttk.Frame(parent)
        convert_frame.grid(row=row, column=0, sticky='ew', pady=10)

        self.convert_btn = ttk.Button(
            convert_frame,
            text="CONVERT",
            command=self.start_conversion,
            style='Convert.TButton'
        )
        self.convert_btn.pack(fill='x', ipady=8)

        self.progress = ttk.Progressbar(
            convert_frame,
            style='Accent.Horizontal.TProgressbar',
            mode='determinate'
        )
        self.progress.pack(fill='x', pady=(8, 4))

        self.progress_label = ttk.Label(convert_frame, text="Progress: 0 / 0 files", style='Count.TLabel')
        self.progress_label.pack(anchor='w')

    def _build_log_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="CONVERSION LOG", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='nsew', pady=(5, 0))

        log_frame = ttk.Frame(lf)
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.log_text = tk.Text(
            log_frame,
            height=8,
            state='disabled',
            bg='#1E1E1E',
            fg='#D4D4D4',
            font=('Consolas', 9),
            borderwidth=1,
            relief='solid',
            insertbackground='#D4D4D4'
        )
        self.log_text.pack(side='left', fill='both', expand=True)

        self.log_text.tag_config('success', foreground='#4EC94E')
        self.log_text.tag_config('error', foreground='#FF6B6B')
        self.log_text.tag_config('info', foreground='#FFD700')

        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scroll.set)

    def on_drop(self, event):
        raw = event.data
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        file_paths = [p[0] if p[0] else p[1] for p in paths]

        added = 0
        for fp in file_paths:
            if fp.lower().endswith('.md') and fp not in self.files:
                self.files.append(fp)
                self.listbox.insert(tk.END, fp)
                added += 1

        if added > 0:
            self.log(f"[->] Dropped {added} file(s) added.")
            self._update_file_count()
        return self.files

    def _update_file_count(self):
        self.count_label.config(text=f"[File count: {len(self.files)}]")

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Markdown files",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if files:
            added = 0
            for f in files:
                if f not in self.files:
                    self.files.append(f)
                    self.listbox.insert(tk.END, f)
                    added += 1
            if added:
                self._update_file_count()

    def remove_selected(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        for index in sorted(selected, reverse=True):
            self.listbox.delete(index)
            del self.files[index]
        self._update_file_count()

    def clear_all(self):
        self.listbox.delete(0, tk.END)
        self.files.clear()
        self._update_file_count()

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_var.set(folder)

    def log(self, message):
        self.log_queue.put(message)

    def _poll_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self._append_log(msg)
        self.root.after(100, self._poll_log_queue)

    def _append_log(self, message):
        self.log_text.config(state='normal')

        if message.startswith('[✔]'):
            tag = 'success'
        elif message.startswith('[✘]'):
            tag = 'error'
        elif message.startswith('[->]'):
            tag = 'info'
        else:
            tag = None

        if tag:
            self.log_text.insert(tk.END, message + '\n', tag)
        else:
            self.log_text.insert(tk.END, message + '\n')

        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_conversion(self):
        if self.is_converting:
            return
        if not self.files:
            self.log("[✘] ERROR: No input files selected.")
            return
        output_dir = self.output_var.get()
        if not output_dir:
            self.log("[✘] ERROR: No output folder selected.")
            return

        self.is_converting = True
        self.convert_btn.config(state='disabled')
        self.progress['value'] = 0

        thread = threading.Thread(target=self._convert_thread, daemon=True)
        thread.start()

    def _convert_thread(self):
        theme = self.theme_var.get()
        output_dir = self.output_var.get()
        open_after = self.open_file_var.get()
        fmt = self.format_var.get()

        jobs = []
        for md_path in self.files[:]:
            if fmt == "PDF":
                jobs.append(('pdf', md_path))
            elif fmt == "DOCX":
                jobs.append(('docx', md_path))
            else:
                jobs.append(('pdf', md_path))
                jobs.append(('docx', md_path))

        total = len(jobs)
        self.root.after(0, lambda: self.progress.config(maximum=total))
        done = 0

        for job_type, md_path in jobs:
            base = os.path.basename(md_path)
            try:
                if job_type == 'pdf':
                    self.log(f"[->] Converting {base} to PDF...")
                    out_path = convert_md_to_pdf(md_path, output_dir, theme)
                    self.log(f"[✔] {base} \u2192 {os.path.basename(out_path)}")
                elif job_type == 'docx':
                    self.log(f"[->] Converting {base} to DOCX...")
                    out_path = convert_md_to_docx(md_path, output_dir)
                    self.log(f"[✔] {base} \u2192 {os.path.basename(out_path)}")

                if open_after:
                    self.log(f"[->] Opening {os.path.basename(out_path)}...")
                    open_file(out_path)
            except Exception as e:
                ext = job_type.upper()
                self.log(f"[✘] ERROR converting {base} to {ext}: {str(e)}")

            done += 1
            self.root.after(0, lambda d=done: self.progress.config(value=d))
            self.root.after(0, lambda d=done, t=total: self.progress_label.config(text=f"Progress: {d} / {t} files"))

        self.log("[✔] Conversion complete.")
        self.root.after(0, self._conversion_done)

    def _conversion_done(self):
        self.is_converting = False
        self.convert_btn.config(state='normal')


def run_app():
    root = TkinterDnD.Tk()
    app = MarkdownConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
