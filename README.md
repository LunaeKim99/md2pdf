# Markdown to PDF Converter

A Python desktop application that converts Markdown files to stylized PDF documents with a graphical user interface.

## Features

- Convert one or multiple Markdown files to PDF
- Multiple themes: Default, Dark, Academic, Minimal
- Option to open PDF after conversion
- Real-time conversion log

## Requirements

- Python 3.10+
- See `requirements.txt` for Python dependencies

## Installation

1. Clone or download this repository.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   (This installs `markdown` and `weasyprint`.)

## Usage

Run the application:
```
python main.py
```
Or directly:
```
python app.py
```

1. Click "Add File(s)" to select Markdown files.
2. Choose an output folder.
3. Select a theme.
4. Optionally check "Open PDF after conversion".
5. Click "Convert".

The log area shows progress and any errors.

## Notes

- The application uses `weasyprint` for PDF generation, which may require additional system libraries (e.g., Cairo, Pango). See [weasyprint documentation](https://weasyprint.readthedocs.io/) for details.
- On Windows, you may need to install GTK. weasyprint may have wheels that include dependencies.
