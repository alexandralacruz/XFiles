"""Tests de división y unión de PDFs."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
import pytest

from xfiles.core.errors import PdfOperationError
from xfiles.core.pdf_ops import merge_pdfs, split_pdf


def make_pdf(path: Path, pages: int = 5) -> None:
    doc = fitz.open()
    for i in range(1, pages + 1):
        page = doc.new_page()
        page.insert_text((72, 72), f"Pagina {i}", fontsize=14)
    doc.save(str(path))
    doc.close()


def page_count(path: Path) -> int:
    doc = fitz.open(str(path))
    try:
        return doc.page_count
    finally:
        doc.close()


def test_split_single(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    make_pdf(src, pages=3)
    produced = split_pdf(src, tmp_path / "out", mode="single")
    assert len(produced) == 3
    assert all(page_count(p) == 1 for p in produced)


def test_split_ranges(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    make_pdf(src, pages=10)
    produced = split_pdf(src, tmp_path / "out", mode="ranges", ranges="1-3, 5, 7-9")
    assert len(produced) == 3
    assert [page_count(p) for p in produced] == [3, 1, 3]


def test_split_every(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    make_pdf(src, pages=10)
    produced = split_pdf(src, tmp_path / "out", mode="every", every=4)
    assert [page_count(p) for p in produced] == [4, 4, 2]


def test_split_invalid_range(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    make_pdf(src, pages=3)
    with pytest.raises(PdfOperationError):
        split_pdf(src, tmp_path / "out", mode="ranges", ranges="1-99")


def test_merge(tmp_path: Path) -> None:
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    make_pdf(a, pages=2)
    make_pdf(b, pages=3)
    out = merge_pdfs([a, b], tmp_path / "merged.pdf")
    assert page_count(out) == 5


def test_merge_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PdfOperationError):
        merge_pdfs([tmp_path / "no-existe.pdf"], tmp_path / "out.pdf")
