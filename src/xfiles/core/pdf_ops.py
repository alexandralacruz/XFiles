"""Operaciones sobre PDFs: dividir y unir."""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf as fitz

from .errors import PdfOperationError


def _write_pages(doc: fitz.Document, pages: list[int], out: Path) -> None:
    new = fitz.open()
    try:
        for index in pages:
            new.insert_pdf(doc, from_page=index, to_page=index)
        new.save(str(out))
    finally:
        new.close()


def _parse_ranges(text: str, page_count: int) -> list[tuple[int, int]]:
    """Parsea `1-3,5,7-9` en una lista de rangos (inicio, fin) inclusivos."""
    specs: list[tuple[int, int]] = []
    for part in re.split(r"[;,\s]+", text or ""):
        part = part.strip()
        if not part:
            continue
        match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
        else:
            match = re.fullmatch(r"(\d+)", part)
            if not match:
                raise PdfOperationError(f"Rango inválido: {part!r}")
            a = b = int(match.group(1))
        if a < 1 or b > page_count or a > b:
            raise PdfOperationError(
                f"Rango fuera de límites (1-{page_count}): {part!r}"
            )
        specs.append((a, b))
    if not specs:
        raise PdfOperationError("No se indicó ningún rango de páginas.")
    return specs


def split_pdf(
    src: str | Path,
    out_dir: str | Path,
    mode: str = "single",
    ranges: str | None = None,
    every: int | None = None,
) -> list[Path]:
    """Divide un PDF.

    Modos:
      - ``single``: un archivo por página.
      - ``ranges``: rangos tipo ``1-3,5,7-9``; cada rango genera un PDF.
      - ``every``: un PDF por cada ``every`` páginas.
    """
    source = Path(src)
    directory = Path(out_dir)
    doc = fitz.open(str(source))
    try:
        total = doc.page_count
        stem = source.stem or "documento"
        directory.mkdir(parents=True, exist_ok=True)

        jobs: list[tuple[str, list[int]]] = []
        if mode == "single":
            jobs = [(f"{stem}_pag{i + 1}", [i]) for i in range(total)]
        elif mode == "every":
            step = int(every or 1)
            if step < 1:
                raise PdfOperationError("'every' debe ser un entero mayor o igual a 1.")
            for start in range(0, total, step):
                end = min(start + step, total)
                jobs.append((f"{stem}_{start + 1}-{end}", list(range(start, end))))
        elif mode == "ranges":
            for a, b in _parse_ranges(ranges or "", total):
                jobs.append((f"{stem}_{a}-{b}", list(range(a - 1, b))))
        else:
            raise PdfOperationError(f"Modo de división desconocido: {mode!r}")

        produced: list[Path] = []
        for label, pages in jobs:
            out = directory / f"{label}.pdf"
            _write_pages(doc, pages, out)
            produced.append(out)
        return produced
    finally:
        doc.close()


def merge_pdfs(paths: list[str | Path], dst: str | Path) -> Path:
    """Une varios PDFs en uno solo, respetando el orden indicado."""
    if not paths:
        raise PdfOperationError("No se indicaron archivos para unir.")
    target = Path(dst)
    target.parent.mkdir(parents=True, exist_ok=True)

    merged = fitz.open()
    try:
        for path in paths:
            p = Path(path)
            if not p.exists():
                raise PdfOperationError(f"No existe el archivo: {p}")
            with fitz.open(str(p)) as src:
                merged.insert_pdf(src)
        merged.save(str(target))
    finally:
        merged.close()
    return target
