# app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import queue
import os
import sys
import subprocess
import json
import logging
import logging.handlers
from datetime import date
from converter import convert_md_to_pdf, convert_md_to_docx, apply_template

VERSION = "v1.3.0"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".md2pdf_config.json")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_DIR, "md2pdf.log")


def open_file(path):
    """Open a file with the default system viewer."""
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.call(['open', path])
    else:
        subprocess.call(['xdg-open', path])


class GUILogHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        msg = self.format(record)
        self.queue.put(msg)


class MarkdownConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"MD to PDF / DOCX Converter {VERSION}")
        self.root.minsize(950, 560)
        self.root.geometry("1100x620")
        self.root.configure(bg='#F7F9FC')
        self.root.resizable(True, True)

        self.files = []
        self.log_queue = queue.Queue()
        self.is_converting = False

        self._setup_logger()
        self._load_config()
        self._setup_styles()
        self._setup_ui()
        self._apply_saved_config()
        self._poll_log_queue()

    def _setup_logger(self):
        self.logger = logging.getLogger("md2pdf")
        self.logger.setLevel(logging.DEBUG)
        gui_handler = GUILogHandler(self.log_queue)
        gui_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(gui_handler)

        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=500 * 1024, backupCount=2, encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self.logger.addHandler(file_handler)

    def _load_config(self):
        self.config = {"recent_files": [], "last_output_dir": "", "last_theme": "Default", "last_format": "PDF"}
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception:
                pass

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _apply_saved_config(self):
        if self.config.get("last_output_dir"):
            self.output_var.set(self.config["last_output_dir"])
        if self.config.get("last_theme"):
            self.theme_var.set(self.config["last_theme"])
        if self.config.get("last_format"):
            self.format_var.set(self.config["last_format"])

    def _update_recent_files(self, md_paths):
        recent = self.config.get("recent_files", [])
        for p in md_paths:
            if p in recent:
                recent.remove(p)
            recent.insert(0, p)
        self.config["recent_files"] = recent[:10]
        self._save_config()

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

        style.configure('OptEntry.TEntry', font=('Segoe UI', 10))
        style.configure('Opt.TLabel', font=('Segoe UI', 10))
        style.configure('Opt.TCombobox', font=('Segoe UI', 10))
        style.configure('Check.TCheckbutton', font=('Segoe UI', 10))
        style.configure('Recent.TButton', background='#2E86AB', foreground='white', font=('Segoe UI', 9))
        style.map('Recent.TButton',
                  background=[('active', '#1A6A8C'), ('pressed', '#1A6A8C')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        style.configure('SaveLog.TButton', background='#555555', foreground='white', font=('Segoe UI', 9))
        style.map('SaveLog.TButton',
                  background=[('active', '#333333'), ('pressed', '#333333')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        style.configure('ClearLog.TButton', background='#888888', foreground='white', font=('Segoe UI', 9))
        style.map('ClearLog.TButton',
                  background=[('active', '#666666'), ('pressed', '#666666')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill='both', expand=True)

        main_frame.grid_columnconfigure(0, weight=2, minsize=380)
        main_frame.grid_columnconfigure(1, weight=3, minsize=460)
        main_frame.grid_rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame, padding=(0, 0, 10, 0))
        left_frame.grid(row=0, column=0, sticky='nsew')

        right_frame = ttk.Frame(main_frame, padding=(10, 0, 0, 0))
        right_frame.grid(row=0, column=1, sticky='nsew')

        self._build_left_panel(left_frame)
        self._build_right_panel(right_frame)

    def _build_left_panel(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self._build_header(parent, 0)
        self._build_input_section(parent, 1)
        self._build_options_section(parent, 2)

    def _build_right_panel(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=0)
        parent.grid_rowconfigure(4, weight=0)
        parent.grid_columnconfigure(0, weight=1)

        self._build_log_section(parent, 0)
        ttk.Separator(parent, orient='horizontal').grid(row=1, column=0, sticky='ew', pady=8)
        self._build_output_section(parent, 2)
        ttk.Separator(parent, orient='horizontal').grid(row=3, column=0, sticky='ew', pady=8)
        self._build_convert_section(parent, 4)

    def _build_header(self, parent, row):
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=row, column=0, sticky='ew', pady=(0, 10))

        ttk.Label(header_frame, text=f"\U0001F4C4 MD \u2192 PDF / DOCX Converter {VERSION}",
                  style='Header.TLabel').pack(anchor='w')
        ttk.Label(header_frame, text="Convert Markdown to styled PDF or DOCX",
                  style='Subtitle.TLabel').pack(anchor='w')

    def _build_input_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="INPUT FILES", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='nsew', pady=(0, 10))
        lf.grid_rowconfigure(0, weight=1)
        lf.grid_columnconfigure(0, weight=1)

        content_frame = ttk.Frame(lf)
        content_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 5))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        list_frame = ttk.Frame(content_frame)
        list_frame.grid(row=0, column=0, sticky='nsew')
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            height=10,
            bg='#FFFFFF',
            selectbackground='#2E86AB',
            selectforeground='white',
            font=('Segoe UI', 10),
            borderwidth=1,
            relief='solid'
        )
        self.listbox.grid(row=0, column=0, sticky='nsew')

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)

        hint_frame = ttk.Frame(content_frame)
        hint_frame.grid(row=1, column=0, sticky='ew', pady=(0, 5))
        hint_frame.grid_columnconfigure(0, weight=1)
        hint_frame.grid_columnconfigure(1, weight=1)

        self.hint_label = ttk.Label(hint_frame, text="\U0001F4A1 Drag & drop .md files here", style='Hint.TLabel')
        self.hint_label.grid(row=0, column=0, sticky='w')

        self.count_label = ttk.Label(hint_frame, text="[File count: 0]", style='Count.TLabel')
        self.count_label.grid(row=0, column=1, sticky='e')

        btn_frame = ttk.Frame(content_frame)
        btn_frame.grid(row=2, column=0, sticky='ew')
        btn_frame.grid_columnconfigure(0, weight=1)

        inner_btn = ttk.Frame(btn_frame)
        inner_btn.grid(row=0, column=0, sticky='w')

        ttk.Button(inner_btn, text="Add Files", command=self.add_files).pack(side='left', padx=(0, 5))
        ttk.Button(inner_btn, text="Remove Selected", command=self.remove_selected).pack(side='left', padx=(0, 5))
        ttk.Button(inner_btn, text="Recent Files", command=self.show_recent_files, style='Recent.TButton').pack(side='left', padx=(0, 5))
        ttk.Button(inner_btn, text="Clear All", command=self.clear_all).pack(side='left')

    def _build_options_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="OPTIONS", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='ew', pady=(0, 5))

        opts_frame = ttk.Frame(lf)
        opts_frame.pack(fill='x', padx=10, pady=10)

        row1 = ttk.Frame(opts_frame)
        row1.pack(fill='x', pady=(0, 5))

        ttk.Label(row1, text="Theme:", style='Opt.TLabel').pack(side='left', padx=(0, 5))
        self.theme_var = tk.StringVar(value="Default")
        theme_combo = ttk.Combobox(
            row1,
            textvariable=self.theme_var,
            values=["Default", "Dark", "Academic", "Minimal"],
            state="readonly",
            width=16,
            style='Opt.TCombobox'
        )
        theme_combo.pack(side='left', padx=(0, 15))

        ttk.Label(row1, text="Format:", style='Opt.TLabel').pack(side='left', padx=(0, 5))
        self.format_var = tk.StringVar(value="PDF")
        format_combo = ttk.Combobox(
            row1,
            textvariable=self.format_var,
            values=["PDF", "DOCX", "Both"],
            state="readonly",
            width=16,
            style='Opt.TCombobox'
        )
        format_combo.pack(side='left', padx=(0, 10))

        self.open_file_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            row1,
            text="Open file after conversion",
            variable=self.open_file_var,
            style='Check.TCheckbutton'
        ).pack(side='left')

        row2 = ttk.Frame(opts_frame)
        row2.pack(fill='x', pady=(0, 3))

        ttk.Label(row2, text="Output name:", style='Opt.TLabel').pack(side='left', padx=(0, 5))
        self.template_var = tk.StringVar(value="{filename}")
        ttk.Entry(row2, textvariable=self.template_var, width=28, style='OptEntry.TEntry').pack(side='left', padx=(0, 10))

        ttk.Label(row2, text="Placeholders: {filename} {date} {index}", style='Hint.TLabel').pack(side='left')

    def _build_log_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="CONVERSION LOG", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='nsew')
        lf.grid_rowconfigure(0, weight=1)
        lf.grid_columnconfigure(0, weight=1)

        log_inner = ttk.Frame(lf)
        log_inner.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        log_inner.grid_rowconfigure(0, weight=1)
        log_inner.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_inner,
            height=15,
            state='disabled',
            bg='#1E1E1E',
            fg='#D4D4D4',
            font=('Consolas', 9),
            borderwidth=1,
            relief='solid',
            insertbackground='#D4D4D4'
        )
        self.log_text.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.log_text.tag_config('success', foreground='#4EC94E')
        self.log_text.tag_config('error', foreground='#FF6B6B')
        self.log_text.tag_config('info', foreground='#FFD700')

        log_scroll = ttk.Scrollbar(log_inner, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.grid(row=0, column=2, sticky='ns')
        self.log_text.config(yscrollcommand=log_scroll.set)

        log_btn_frame = ttk.Frame(log_inner)
        log_btn_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(8, 0))

        ttk.Button(log_btn_frame, text="\U0001F4BE Save Log", command=self.save_log, style='SaveLog.TButton').pack(side='left')
        ttk.Button(log_btn_frame, text="Clear Log", command=self.clear_log, style='ClearLog.TButton').pack(side='right')

    def _build_output_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="OUTPUT FOLDER", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='ew')

        output_frame = ttk.Frame(lf)
        output_frame.pack(fill='x', padx=10, pady=10)

        self.output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_var, style='OptEntry.TEntry').pack(
            side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side='left')

    def _build_convert_section(self, parent, row):
        convert_frame = ttk.Frame(parent)
        convert_frame.grid(row=row, column=0, sticky='ew')

        self.convert_btn = ttk.Button(
            convert_frame,
            text="CONVERT",
            command=self.start_conversion,
            style='Convert.TButton'
        )
        self.convert_btn.pack(fill='x', ipady=10)

        self.progress = ttk.Progressbar(
            convert_frame,
            style='Accent.Horizontal.TProgressbar',
            mode='determinate'
        )
        self.progress.pack(fill='x', pady=(8, 4))

        self.progress_label = ttk.Label(convert_frame, text="Progress: 0 / 0 files", style='Count.TLabel')
        self.progress_label.pack(anchor='w')

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

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')

    def on_drop(self, event):
        try:
            file_paths = self.root.tk.splitlist(event.data)
        except Exception:
            file_paths = event.data.split()

        added = 0
        for fp in file_paths:
            fp = fp.strip()
            if fp.lower().endswith('.md') and fp not in self.files:
                self.files.append(fp)
                self.listbox.insert(tk.END, fp)
                added += 1

        if added > 0:
            self.logger.info(f"[->] Dropped {added} file(s) added.")
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

    def save_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Save Log"
        )
        if not path:
            return
        content = self.log_text.get(1.0, tk.END).strip()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Success", f"Log saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")

    def show_recent_files(self):
        popup = tk.Toplevel(self.root)
        popup.title("Recent Files")
        popup.geometry("500x300")
        popup.configure(bg='#F7F9FC')
        popup.transient(self.root)
        popup.grab_set()

        listbox = tk.Listbox(
            popup,
            bg='#1E1E1E',
            fg='#D4D4D4',
            font=('Consolas', 9),
            selectbackground='#2E86AB',
            selectforeground='white',
            borderwidth=1,
            relief='solid'
        )
        listbox.pack(fill='both', expand=True, padx=10, pady=10)

        recent = self.config.get("recent_files", [])
        for fp in recent:
            listbox.insert(tk.END, fp)

        btn_frame = ttk.Frame(popup)
        btn_frame.pack(fill='x', padx=10, pady=(0, 10))

        def add_selected():
            selected = listbox.curselection()
            if not selected:
                return
            added = 0
            for idx in selected:
                fp = listbox.get(idx)
                if os.path.exists(fp) and fp not in self.files:
                    self.files.append(fp)
                    self.listbox.insert(tk.END, fp)
                    added += 1
            if added:
                self._update_file_count()
            popup.destroy()

        def clear_history():
            self.config["recent_files"] = []
            self._save_config()
            listbox.delete(0, tk.END)

        ttk.Button(btn_frame, text="Add to List", command=add_selected).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Clear History", command=clear_history).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Close", command=popup.destroy).pack(side='right')

    def start_conversion(self):
        if self.is_converting:
            return
        if not self.files:
            self.logger.info("[\u2718] ERROR: No input files selected.")
            return
        output_dir = self.output_var.get().strip()
        if not output_dir:
            self.logger.info("[\u2718] ERROR: No output folder selected.")
            return
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            self.logger.info(f"[\u2718] ERROR: Cannot create output folder: {e}")
            return

        self.is_converting = True
        self.convert_btn.config(state='disabled')
        self.progress['value'] = 0

        thread = threading.Thread(target=self._convert_thread, daemon=True)
        thread.start()

    def _convert_thread(self):
        theme = self.theme_var.get()
        output_dir = self.output_var.get().strip()
        open_after = self.open_file_var.get()
        fmt = self.format_var.get()
        template = self.template_var.get().strip() or "{filename}"

        self.config["last_output_dir"] = output_dir
        self.config["last_theme"] = theme
        self.config["last_format"] = fmt
        self._save_config()

        jobs = []
        for idx, md_path in enumerate(self.files[:], start=1):
            base = os.path.splitext(os.path.basename(md_path))[0]
            out_name = apply_template(template, base, idx)
            if fmt in ("PDF", "Both"):
                jobs.append(('pdf', md_path, out_name))
            if fmt in ("DOCX", "Both"):
                jobs.append(('docx', md_path, out_name))

        total = len(jobs)
        self.root.after(0, lambda: self.progress.config(maximum=total))
        done = 0
        converted_files = []

        for job_type, md_path, out_name in jobs:
            base = os.path.basename(md_path)
            try:
                if job_type == 'pdf':
                    self.logger.info(f"[->] Converting {base} to PDF...")
                    out_path = convert_md_to_pdf(md_path, output_dir, theme, out_name)
                    self.logger.info(f"[\u2714] {base} \u2192 {os.path.basename(out_path)}")
                elif job_type == 'docx':
                    self.logger.info(f"[->] Converting {base} to DOCX...")
                    out_path = convert_md_to_docx(md_path, output_dir, out_name)
                    self.logger.info(f"[\u2714] {base} \u2192 {os.path.basename(out_path)}")

                converted_files.append(md_path)

                if open_after:
                    self.logger.info(f"[->] Opening {os.path.basename(out_path)}...")
                    open_file(out_path)
            except Exception as e:
                ext = job_type.upper()
                self.logger.info(f"[\u2718] ERROR converting {base} to {ext}: {str(e)}")

            done += 1
            self.root.after(0, lambda d=done: self.progress.config(value=d))
            self.root.after(0, lambda d=done, t=total: self.progress_label.config(text=f"Progress: {d} / {t} files"))

        if converted_files:
            self._update_recent_files(converted_files)

        self.logger.info("[\u2714] Conversion complete.")
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
