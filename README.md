# 📄 MD → PDF / DOCX Converter

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/LunaeKim99/md2pdf)

A modern desktop application that converts Markdown files to styled PDF or DOCX documents with a clean GUI.

---

## ✨ Features

- **PDF Export** — Convert Markdown to styled PDF using WeasyPrint
- **DOCX Export** — Convert Markdown to Word documents using python-docx
- **Batch Processing** — Convert multiple files at once
- **Drag & Drop** — Drag `.md` files directly onto the file list
- **4 Built-in Themes** — Default, Dark, Academic, Minimal
- **Output Templates** — Custom filename patterns with `{filename}`, `{date}`, `{index}` placeholders
- **Recent Files** — Quick access to your last 10 converted files
- **Log Export** — Save conversion logs to a text file
- **Auto-Open** — Optionally open output files after conversion
- **Persistent Settings** — Remembers last output folder, theme, and format

---

## 📦 Installation

```bash
git clone https://github.com/LunaeKim99/md2pdf
cd md2pdf
pip install -r requirements.txt
```

> **Note:** WeasyPrint may require additional system libraries (Cairo, Pango). See [WeasyPrint docs](https://weasyprint.readthedocs.io/) for installation details.

---

## 🚀 Usage

```bash
python main.py
```

### GUI Sections

| Section | Description |
|---|---|
| **Input Files** | Add `.md` files via button or drag & drop. Manage with Add/Remove/Clear. |
| **Recent Files** | Quick-access popup for your last 10 converted files. |
| **Output Folder** | Select where converted files will be saved. |
| **Options** | Choose theme, output format (PDF/DOCX/Both), filename template, and auto-open. |
| **Convert** | Start conversion with progress bar. |
| **Conversion Log** | Real-time log with color-coded status. Export to file with 💾 Save Log. |

---

## 🎨 Themes

| Theme | Description |
|---|---|
| **Default** | Clean, professional look with Segoe UI font |
| **Dark** | Dark background with light text, ideal for code-heavy documents |
| **Academic** | Georgia serif font, justified text, formal style |
| **Minimal** | Lightweight, minimal styling with generous line spacing |

---

## 📝 Output Templates

Customize output filenames using placeholders:

| Template | Example Output |
|---|---|
| `{filename}` | `notes.pdf` |
| `{date}_{filename}` | `2026-05-07_notes.pdf` |
| `{index}_{filename}` | `01_notes.pdf` |
| `{date}_{index}_{filename}` | `2026-05-07_01_notes.pdf` |

---

## 📁 Project Structure

```
md2pdf/
├── main.py            # Entry point
├── app.py             # Tkinter GUI application
├── converter.py       # PDF and DOCX conversion logic
├── themes.py          # CSS theme definitions
├── requirements.txt   # Python dependencies
├── tests/
│   └── test_converter.py  # Unit tests
└── README.md          # This file
```

---

## 📋 Requirements

- Python 3.10+
- `markdown` — Markdown to HTML conversion
- `weasyprint` — HTML/CSS to PDF rendering
- `python-docx` — DOCX document creation
- `tkinterdnd2` — Drag and drop support for Tkinter
- `beautifulsoup4` — HTML parsing for DOCX conversion
- `pytest` — Testing framework

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
