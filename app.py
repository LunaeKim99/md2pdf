# app.py
import tkinter as tk
from tkinter import ttk, filedialog
import threading
import queue
import os
import sys
import subprocess
from converter import convert_md_to_pdf

def open_pdf(path):
    """Open a PDF file with the default system viewer."""
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.call(['open', path])
    else:
        subprocess.call(['xdg-open', path])

class MarkdownConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown to PDF Converter")
        self.root.minsize(700, 550)
        
        self.files = []  # list of selected markdown file paths
        self.log_queue = queue.Queue()
        
        self.setup_ui()
        self.poll_log_queue()
        
    def setup_ui(self):
        # Input frame
        input_frame = ttk.LabelFrame(self.root, text="Input Files")
        input_frame.pack(fill='x', padx=10, pady=5)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(input_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=6)
        self.listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons for file management
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Add File(s)", command=self.add_files).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side='left', padx=5)
        
        # Output folder frame
        output_frame = ttk.LabelFrame(self.root, text="Output Folder")
        output_frame.pack(fill='x', padx=10, pady=5)
        
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        output_entry.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        ttk.Button(output_frame, text="Browse Output Folder", command=self.browse_output).pack(side='left', padx=5, pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(self.root, text="Options")
        options_frame.pack(fill='x', padx=10, pady=5)
        
        # Theme selection
        ttk.Label(options_frame, text="Theme:").pack(side='left', padx=5, pady=5)
        self.theme_var = tk.StringVar(value="Default")
        theme_combo = ttk.Combobox(options_frame, textvariable=self.theme_var, 
                                   values=["Default", "Dark", "Academic", "Minimal"],
                                   state="readonly", width=15)
        theme_combo.pack(side='left', padx=5, pady=5)
        
        # Checkbox for opening PDF
        self.open_pdf_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Open PDF after conversion", variable=self.open_pdf_var).pack(side='left', padx=20, pady=5)
        
        # Convert button
        convert_frame = ttk.Frame(self.root)
        convert_frame.pack(pady=10)
        convert_btn = ttk.Button(convert_frame, text="Convert", command=self.start_conversion)
        # Make button prominent with padding
        convert_btn.pack(ipadx=20, ipady=10)
        
        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, state='disabled')
        self.log_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scroll.set)
        
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Markdown files",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if files:
            for f in files:
                if f not in self.files:
                    self.files.append(f)
                    self.listbox.insert(tk.END, f)
    
    def remove_selected(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        # Remove from end to avoid index shifting
        for index in sorted(selected, reverse=True):
            self.listbox.delete(index)
            del self.files[index]
    
    def clear_all(self):
        self.listbox.delete(0, tk.END)
        self.files.clear()
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_var.set(folder)
    
    def log(self, message):
        self.log_queue.put(message)
    
    def poll_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, msg + '\n')
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        self.root.after(100, self.poll_log_queue)
    
    def start_conversion(self):
        # Validate
        if not self.files:
            self.log("ERROR: No input files selected.")
            return
        output_dir = self.output_var.get()
        if not output_dir:
            self.log("ERROR: No output folder selected.")
            return
        
        # Start conversion thread
        thread = threading.Thread(target=self.convert_thread, daemon=True)
        thread.start()
    
    def convert_thread(self):
        theme = self.theme_var.get()
        output_dir = self.output_var.get()
        open_after = self.open_pdf_var.get()
        
        for md_path in self.files[:]:
            try:
                self.log(f"Converting {os.path.basename(md_path)}...")
                pdf_path = convert_md_to_pdf(md_path, output_dir, theme)
                self.log(f"Done: {os.path.basename(md_path)} -> {pdf_path}")
                if open_after:
                    self.log(f"Opening {pdf_path}...")
                    open_pdf(pdf_path)
            except Exception as e:
                self.log(f"ERROR converting {md_path}: {str(e)}")
        
        self.log("Conversion complete.")

def run_app():
    root = tk.Tk()
    app = MarkdownConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()
