"""Autodiagnóstico de las conversiones (smoke test del binario empaquetado)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pymupdf as fitz

from xfiles.core.converter import convert
from xfiles.core.pdf_ops import merge_pdfs, split_pdf


def run() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)

        pdf = d / "a.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Titulo de prueba", fontsize=20)
        page.insert_text((72, 130), "Parrafo de prueba con acentos.", fontsize=12)
        doc.save(str(pdf))
        doc.close()

        convert(pdf, d / "a.md")
        convert(pdf, d / "a.txt")
        convert(pdf, d / "a.docx")
        convert(d / "a.md", d / "b.pdf")      # MD -> PDF (WeasyPrint/xhtml2pdf)
        convert(d / "a.txt", d / "c.pdf")     # TXT -> PDF (fpdf2)
        convert(d / "a.docx", d / "a2.txt")   # DOCX -> TXT
        convert(d / "a.md", d / "a2.docx")    # MD -> DOCX
        split_pdf(pdf, d / "split", mode="single")
        merge_pdfs([pdf, pdf], d / "merged.pdf")

        expected = ("a.md", "a.txt", "a.docx", "b.pdf", "c.pdf", "a2.txt", "a2.docx", "merged.pdf")
        for name in expected:
            if not (d / name).exists():
                raise RuntimeError(f"Falta el archivo de salida: {name}")

        md_text = (d / "a.md").read_text(encoding="utf-8")
        if "Titulo de prueba" not in md_text:
            raise RuntimeError("El Markdown generado no contiene el texto esperado.")

    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
