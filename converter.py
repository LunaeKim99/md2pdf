# converter.py
import os
from markdown import markdown
from weasyprint import HTML
from themes import THEMES

def convert_md_to_pdf(md_path, output_dir, theme_name):
    """Convert a Markdown file to PDF with selected theme."""
    # Read markdown file
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    # Convert Markdown to HTML with extensions
    html_content = markdown(md_text, extensions=['tables', 'fenced_code', 'codehilite', 'toc'])
    
    # Get CSS for selected theme
    css_string = THEMES.get(theme_name, THEMES['Default'])
    
    # Build full HTML document with embedded CSS
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{css_string}
</style>
</head>
<body>
{html_content}
</body>
</html>"""
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine output PDF path
    base_name = os.path.splitext(os.path.basename(md_path))[0]
    pdf_path = os.path.join(output_dir, base_name + '.pdf')
    
    # Convert HTML to PDF
    HTML(string=full_html).write_pdf(pdf_path)
    
    return pdf_path
