"""Tests del motor de conversión."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
import pytest
from docx import Document

from xfiles.core.converter import convert
from xfiles.core.errors import ConversionError


def make_pdf(path: Path, pages: int = 3) -> None:
    doc = fitz.open()
    for i in range(1, pages + 1):
        page = doc.new_page()
        page.insert_text((72, 72), f"Titulo pagina {i}", fontsize=22)
        page.insert_text((72, 130), f"Parrafo {i} con algo de texto.", fontsize=12)
    doc.save(str(path))
    doc.close()


def test_pdf_to_txt(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    make_pdf(src)
    out = tmp_path / "a.txt"
    convert(src, out)
    text = out.read_text(encoding="utf-8")
    assert "Titulo pagina 1" in text
    assert "Parrafo 3" in text


def test_pdf_to_md(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    make_pdf(src)
    out = tmp_path / "a.md"
    convert(src, out)
    text = out.read_text(encoding="utf-8")
    assert "## Titulo pagina 1" in text  # 22pt vs 12pt => h2
    assert "Parrafo 1" in text


def test_pdf_to_docx(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    make_pdf(src)
    out = tmp_path / "a.docx"
    convert(src, out)
    doc = Document(str(out))
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert any("Titulo pagina 1" in h for h in headings)


def test_txt_to_pdf(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_text("Línea uno\n\nLínea dos con acentos: á é í ó ú ñ.", encoding="utf-8")
    out = tmp_path / "a.pdf"
    convert(src, out)
    doc = fitz.open(str(out))
    try:
        text = "".join(page.get_text() for page in doc)
    finally:
        doc.close()
    assert "Línea uno" in text


def test_md_to_pdf(tmp_path: Path) -> None:
    src = tmp_path / "a.md"
    src.write_text("# Título\n\nUn párrafo de ejemplo.\n", encoding="utf-8")
    out = tmp_path / "a.pdf"
    convert(src, out)
    doc = fitz.open(str(out))
    try:
        assert doc.page_count >= 1
    finally:
        doc.close()


def test_docx_to_txt_and_md(tmp_path: Path) -> None:
    doc = Document()
    doc.add_heading("Título del documento", level=1)
    doc.add_paragraph("Un párrafo normal.")
    doc.add_paragraph("Elemento de lista", style="List Bullet")
    src = tmp_path / "a.docx"
    doc.save(str(src))

    txt = tmp_path / "a.txt"
    convert(src, txt)
    assert "Título del documento" in txt.read_text(encoding="utf-8")

    md = tmp_path / "a.md"
    convert(src, md)
    content = md.read_text(encoding="utf-8")
    assert "# Título del documento" in content
    assert "- Elemento de lista" in content


def test_md_to_docx(tmp_path: Path) -> None:
    src = tmp_path / "a.md"
    src.write_text("# Título\n\nTexto normal.\n\n- Item uno\n- Item dos\n", encoding="utf-8")
    out = tmp_path / "a.docx"
    convert(src, out)
    doc = Document(str(out))
    texts = [p.text for p in doc.paragraphs]
    assert any("Título" in t for t in texts)
    assert "Item uno" in texts


def test_txt_to_md(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_text("Hola mundo\n", encoding="utf-8")
    out = tmp_path / "a.md"
    convert(src, out)
    assert "Hola mundo" in out.read_text(encoding="utf-8")


def test_unsupported_conversion(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    make_pdf(src, pages=1)
    with pytest.raises(ConversionError):
        convert(src, tmp_path / "a.xls")


def test_legacy_doc_rejected(tmp_path: Path) -> None:
    src = tmp_path / "a.doc"
    src.write_bytes(b"dummy")
    with pytest.raises(ConversionError):
        convert(src, tmp_path / "a.pdf")
