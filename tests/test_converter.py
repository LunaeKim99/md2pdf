# tests/test_converter.py
import os
import pytest
from datetime import date
from unittest.mock import patch
from markdown import markdown
from converter import convert_md_to_pdf, convert_md_to_docx, apply_template


def test_md_to_html_basic():
    html = markdown("# Hello", extensions=['tables', 'fenced_code', 'codehilite', 'toc'])
    assert '<h1' in html
    assert 'Hello' in html


def test_convert_md_to_pdf_creates_file(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Hello World\n\nThis is a test.")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = convert_md_to_pdf(str(md_file), str(output_dir), "Default")
    assert os.path.exists(result)
    assert result.endswith(".pdf")


def test_convert_md_to_docx_creates_file(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Hello World\n\nThis is a test.")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = convert_md_to_docx(str(md_file), str(output_dir))
    assert os.path.exists(result)
    assert result.endswith(".docx")


def test_output_rename_template():
    with patch("converter.date") as mock_date:
        mock_date.today.return_value = date(2026, 5, 7)

        assert apply_template("{filename}", "notes", 1) == "notes"
        assert apply_template("{date}_{filename}", "notes", 1) == "2026-05-07_notes"
        assert apply_template("{index}_{filename}", "notes", 3) == "03_notes"


def test_recent_files_max_10():
    recent = []
    for i in range(11):
        path = f"file{i}.md"
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:10]

    assert len(recent) == 10
    assert "file10.md" == recent[0]
    assert "file0.md" not in recent
    assert "file1.md" in recent
