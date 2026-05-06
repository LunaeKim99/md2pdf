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
        self.root.minsize(750, 620)
        self.root.configure(bg='#F7F9FC')

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
        style.configure('RecentList.TListbox', background='#1E1E1E', foreground='#D4D4D4',
                        font=('Consolas', 9), selectbackground='#2E86AB', selectforeground='white')

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
        ttk.Button(btn_frame, text="Recent Files", command=self.show_recent_files, style='Recent.TButton').pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side='left', padx=(5, 0))

    def _build_output_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="OUTPUT FOLDER", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='ew', pady=5)

        output_frame = ttk.Frame(lf)
        output_frame.pack(fill='x', padx=10, pady=10)

        self.output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_var, style='OptEntry.TEntry').pack(
            side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side='left')

    def _build_options_section(self, parent, row):
        lf = ttk.LabelFrame(parent, text="OPTIONS", style='Input.TLabelframe')
        lf.grid(row=row, column=0, sticky='ew', pady=5)

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
            width=14,
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
            width=10,
            style='Opt.TCombobox'
        )
        format_combo.pack(side='left', padx=(0, 20))

        self.open_file_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            row1,
            text="Open file after conversion",
            variable=self.open_file_var,
            style='Check.TCheckbutton'
        ).pack(side='left')

        row2 = ttk.Frame(opts_frame)
        row2.pack(fill='x')

        ttk.Label(row2, text="Output name:", style='Opt.TLabel').pack(side='left', padx=(0, 5))
        self.template_var = tk.StringVar(value="{filename}")
        ttk.Entry(row2, textvariable=self.template_var, width=25, style='OptEntry.TEntry').pack(side='left', padx=(0, 10))

        ttk.Label(row2, text="Placeholders: {filename} {date} {index}", style='Hint.TLabel').pack(side='left')

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

        log_header = ttk.Frame(lf)
        log_header.pack(fill='x', padx=10, pady=(10, 0))

        ttk.Label(log_header, text="Log output:", style='Hint.TLabel').pack(side='left')
        ttk.Button(log_header, text="\U0001F4BE Save Log", command=self.save_log, style='SaveLog.TButton').pack(side='right')

        log_frame = ttk.Frame(lf)
        log_frame.pack(fill='both', expand=True, padx=10, pady=(5, 10))

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
