"""Extracción estructurada de texto desde PDFs.

Convierte el contenido textual de un PDF en una lista de bloques clasificados
(títulos, párrafos y listas) usando heurísticas de tamaño y grosor de fuente.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz

_BOLD_FLAG = 16  # bit 4 de los flags de PyMuPDF


@dataclass
class Block:
    """Un bloque de texto clasificado."""

    kind: str  # "h1", "h2", "h3", "h4", "list" o "para"
    text: str


def _looks_like_list(text: str) -> bool:
    if re.match(r"^\s*([•▪◦‣●○··]|[-*+])\s+", text):
        return True
    if re.match(r"^\s*(\d{1,3}[.)]|[a-zA-Z][.)])\s+", text):
        return True
    return False


def _classify(size: float, body: float, bold: bool, text: str) -> str:
    ratio = size / body if body else 1.0
    if ratio >= 1.9:
        return "h1"
    if ratio >= 1.6:
        return "h2"
    if ratio >= 1.35:
        return "h3"
    if ratio >= 1.18 or bold:
        return "h4"
    if _looks_like_list(text):
        return "list"
    return "para"


def extract_blocks(path: str | Path) -> list[Block]:
    """Extrae y clasifica los bloques de texto de un PDF.

    Si el PDF no contiene texto extraíble (p. ej. está escaneado), devuelve
    una lista vacía.
    """
    doc = fitz.open(str(path))
    raw: list[tuple[float, bool, str]] = []
    try:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                lines = block.get("lines", [])
                if not lines:
                    continue
                spans = [s for line in lines for s in line.get("spans", [])]
                if not spans:
                    continue
                text = " ".join(
                    "".join(s["text"] for s in line["spans"]) for line in lines
                )
                text = re.sub(r"\s+", " ", text).strip()
                if not text:
                    continue
                size = max(s["size"] for s in spans)
                bold = any(s["flags"] & _BOLD_FLAG for s in spans)
                raw.append((size, bold, text))
    finally:
        doc.close()

    if not raw:
        return []

    # El tamaño del texto "normal" es el que más caracteres acumula
    # (más robusto que la mediana cuando hay muchos títulos/listas).
    weighted: dict[float, int] = {}
    for size, _bold, text in raw:
        weighted[size] = weighted.get(size, 0) + len(text)
    body = max(weighted, key=weighted.get)

    return [
        Block(kind=_classify(size, body, bold, text), text=text)
        for size, bold, text in raw
    ]
