"""Motor de conversiones de XFiles.

Matriz soportada (v1):

    PDF  -> TXT, MD, DOCX
    DOCX -> PDF, TXT, MD
    TXT  -> PDF, MD, DOCX
    MD   -> PDF, TXT, DOCX
"""

from __future__ import annotations

import html as html_lib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pymupdf as fitz
import markdown as markdown_lib
from docx import Document
from fpdf import FPDF

from .errors import ConversionError
from .structure import Block, extract_blocks

OUTPUT_FORMATS: dict[str, str] = {
    "pdf": "PDF (.pdf)",
    "docx": "Word (.docx)",
    "txt": "Texto plano (.txt)",
    "md": "Markdown (.md)",
}

INPUT_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx", ".txt", ".md", ".markdown")

_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: 'DejaVu Sans', 'Segoe UI', sans-serif; font-size: 11pt;
       line-height: 1.55; color: #1f2937; }
h1, h2, h3, h4, h5, h6 { color: #111827; }
pre { background: #f3f4f6; padding: 10px; border-radius: 6px;
      white-space: pre-wrap; font-family: 'DejaVu Sans Mono', 'Consolas', monospace;
      font-size: 9pt; }
code { font-family: 'DejaVu Sans Mono', 'Consolas', monospace; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; }
th, td { border: 1px solid #9ca3af; padding: 4px 8px; text-align: left; }
th { background: #eef2ff; }
"""


# --------------------------------------------------------------------------- #
# Helpers genéricos
# --------------------------------------------------------------------------- #
def _read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _write(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def _fmt(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".markdown":
        return "md"
    if ext == ".doc":
        raise ConversionError(
            "El formato .doc (Word 97-2003) no está soportado. "
            "Guarda el archivo como .docx e inténtalo de nuevo."
        )
    return ext.lstrip(".")


def _block_to_md(block: Block) -> str:
    level = {"h1": 1, "h2": 2, "h3": 3, "h4": 4}.get(block.kind)
    if level:
        return "#" * level + " " + block.text
    if block.kind == "list":
        return "- " + block.text
    return block.text


def _is_windows() -> bool:
    return sys.platform == "win32"


# --------------------------------------------------------------------------- #
# PDF -> X
# --------------------------------------------------------------------------- #
def pdf_to_txt(src: str | Path, dst: str | Path) -> None:
    blocks = extract_blocks(src)
    if not blocks:
        raise ConversionError(
            "No se pudo extraer texto del PDF. Es posible que esté escaneado "
            "como imagen (se necesitaría OCR)."
        )
    _write(dst, "\n\n".join(b.text for b in blocks) + "\n")


def pdf_to_md(src: str | Path, dst: str | Path) -> None:
    blocks = extract_blocks(src)
    if not blocks:
        raise ConversionError(
            "No se pudo extraer texto del PDF. Es posible que esté escaneado "
            "como imagen (se necesitaría OCR)."
        )
    _write(dst, "\n\n".join(_block_to_md(b) for b in blocks) + "\n")


def pdf_to_docx(src: str | Path, dst: str | Path) -> None:
    blocks = extract_blocks(src)
    if not blocks:
        raise ConversionError(
            "No se pudo extraer texto del PDF. Es posible que esté escaneado "
            "como imagen (se necesitaría OCR)."
        )
    doc = Document()
    for block in blocks:
        level = {"h1": 1, "h2": 2, "h3": 3, "h4": 4}.get(block.kind)
        if level:
            doc.add_heading(block.text, level=level)
        elif block.kind == "list":
            doc.add_paragraph(block.text, style="List Bullet")
        else:
            doc.add_paragraph(block.text)
    doc.save(str(dst))


# --------------------------------------------------------------------------- #
# TXT -> PDF / MD -> PDF / DOCX -> PDF
# --------------------------------------------------------------------------- #
def _resolve_fonts() -> tuple[str | None, str | None]:
    """Busca fuentes TTF con soporte Unicode en el sistema."""
    candidates = [
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf"),
        ("/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/SFNS.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists():
            return regular, (bold if Path(bold).exists() else regular)
    return None, None


def _write_text_pdf(text: str, dst: str | Path) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    regular, bold = _resolve_fonts()
    if regular:
        pdf.add_font("Body", "", regular)
        if bold and bold != regular:
            pdf.add_font("Body", "B", bold)
        pdf.set_font("Body", size=11)
    else:
        pdf.set_font("Helvetica", size=11)
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            pdf.ln(5)
            continue
        pdf.multi_cell(0, 6, line)
    pdf.output(str(dst))


def txt_to_pdf(src: str | Path, dst: str | Path) -> None:
    _write_text_pdf(_read_text(src), dst)


def _md_to_html(text: str) -> str:
    body = markdown_lib.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"]
    )
    return (
        "<html><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style></head><body>{body}</body></html>"
    )


def _render_html(html: str, dst: Path) -> None:
    errors: list[str] = []
    try:
        from weasyprint import HTML

        HTML(string=html).write_pdf(str(dst))
        return
    except Exception as exc:  # noqa: BLE001
        errors.append(f"WeasyPrint: {exc}")

    try:
        from xhtml2pdf import pisa

        with open(dst, "wb") as fh:
            status = pisa.CreatePDF(html, dest=fh)
        if status.err:
            errors.append(f"xhtml2pdf: {status.err}")
            raise ConversionError("No se pudo renderizar a PDF. " + "; ".join(errors))
        return
    except ConversionError:
        raise
    except Exception as exc:  # noqa: BLE001
        errors.append(f"xhtml2pdf: {exc}")

    raise ConversionError("No se pudo renderizar a PDF. " + "; ".join(errors))


def md_to_pdf(src: str | Path, dst: str | Path) -> None:
    _render_html(_md_to_html(_read_text(src)), Path(dst))


def _find_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in (
        "C:/Program Files/LibreOffice/program/soffice.exe",
        "C:/Program Files (x86)/LibreOffice/program/soffice.exe",
    ):
        if Path(candidate).exists():
            return candidate
    return None


def docx_to_pdf(src: str | Path, dst: str | Path) -> None:
    src_path = Path(src)
    dst_path = Path(dst)

    # 1) Windows con Microsoft Word instalado (mejor fidelidad).
    if _is_windows():
        try:
            from docx2pdf import convert

            convert(str(src_path), str(dst_path))
            if dst_path.exists():
                return
        except Exception:  # noqa: BLE001
            pass

    # 2) LibreOffice en modo headless (mejor opción multiplataforma).
    soffice = _find_soffice()
    if soffice:
        out_dir = dst_path.parent
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(src_path)],
            check=True,
            capture_output=True,
        )
        produced = out_dir / (src_path.stem + ".pdf")
        if produced.exists():
            if produced != dst_path:
                shutil.move(str(produced), str(dst_path))
            return
        raise ConversionError("LibreOffice no generó el PDF de salida.")

    # 3) Respaldo: extraer el texto y generar un PDF plano.
    doc = Document(str(src_path))
    text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if not text.strip():
        raise ConversionError(
            "El documento no contiene texto y no se encontró LibreOffice ni "
            "Microsoft Word para convertirlo."
        )
    _write_text_pdf(text, dst_path)


# --------------------------------------------------------------------------- #
# DOCX -> TXT / MD
# --------------------------------------------------------------------------- #
def _iter_docx_blocks(path: str | Path) -> list[Block]:
    doc = Document(str(path))
    blocks: list[Block] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name or "").lower()
        if style.startswith("heading"):
            try:
                level = int(style.split()[-1])
            except ValueError:
                level = 2
            blocks.append(Block(kind=f"h{min(level, 4)}", text=text))
        elif "bullet" in style or "list" in style or "number" in style:
            blocks.append(Block(kind="list", text=text))
        else:
            blocks.append(Block(kind="para", text=text))
    return blocks


def docx_to_txt(src: str | Path, dst: str | Path) -> None:
    blocks = _iter_docx_blocks(src)
    if not blocks:
        raise ConversionError("El documento no contiene texto.")
    _write(dst, "\n\n".join(b.text for b in blocks) + "\n")


def docx_to_md(src: str | Path, dst: str | Path) -> None:
    blocks = _iter_docx_blocks(src)
    if not blocks:
        raise ConversionError("El documento no contiene texto.")
    _write(dst, "\n\n".join(_block_to_md(b) for b in blocks) + "\n")


# --------------------------------------------------------------------------- #
# TXT / MD -> otros formatos de texto
# --------------------------------------------------------------------------- #
def txt_to_md(src: str | Path, dst: str | Path) -> None:
    text = _read_text(src)
    lines = []
    for line in text.splitlines():
        # Evita que líneas que empiezan con caracteres de Markdown se
        # interpreten como títulos o listas.
        line = re.sub(r"^(\s{0,3})(#{1,6}\s|[-*+]\s|>|\d+[.)]\s)", r"\1\\\2", line)
        lines.append(line)
    _write(dst, "\n".join(lines) + "\n")


def md_to_txt(src: str | Path, dst: str | Path) -> None:
    html = _md_to_html(_read_text(src))
    plain = re.sub(r"<[^>]+>", "", html)
    plain = html_lib.unescape(plain)
    plain = re.sub(r"[ \t]+\n", "\n", plain)
    plain = re.sub(r"\n{3,}", "\n\n", plain).strip()
    _write(dst, plain + "\n")


def _paragraphs_from_text(text: str) -> list[str]:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(parts) <= 1:
        parts = [l.strip() for l in text.splitlines() if l.strip()]
    return parts


def txt_to_docx(src: str | Path, dst: str | Path) -> None:
    doc = Document()
    for para in _paragraphs_from_text(_read_text(src)):
        doc.add_paragraph(para)
    doc.save(str(dst))


def md_to_docx(src: str | Path, dst: str | Path) -> None:
    doc = Document()
    in_code = False
    for raw in _read_text(src).splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            doc.add_paragraph(raw)
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            doc.add_heading(heading.group(2).strip(), level=min(len(heading.group(1)), 4))
        elif re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
            text = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", line)
            doc.add_paragraph(text, style="List Bullet")
        elif line.strip():
            doc.add_paragraph(line.strip())
    doc.save(str(dst))


# --------------------------------------------------------------------------- #
# Despachador
# --------------------------------------------------------------------------- #
_CONVERTERS: dict[tuple[str, str], object] = {
    ("pdf", "txt"): pdf_to_txt,
    ("pdf", "md"): pdf_to_md,
    ("pdf", "docx"): pdf_to_docx,
    ("docx", "pdf"): docx_to_pdf,
    ("docx", "txt"): docx_to_txt,
    ("docx", "md"): docx_to_md,
    ("txt", "pdf"): txt_to_pdf,
    ("txt", "md"): txt_to_md,
    ("txt", "docx"): txt_to_docx,
    ("md", "pdf"): md_to_pdf,
    ("md", "txt"): md_to_txt,
    ("md", "docx"): md_to_docx,
}


def convert(src: str | Path, dst: str | Path) -> Path:
    """Convierte `src` a `dst` detectando el formato por la extensión."""
    source = Path(src)
    target = Path(dst)
    if not source.exists():
        raise ConversionError(f"No existe el archivo: {source}")

    from_fmt = _fmt(source)
    to_fmt = _fmt(target)
    fn = _CONVERTERS.get((from_fmt, to_fmt))
    if fn is None:
        raise ConversionError(f"Conversión no soportada: {from_fmt} → {to_fmt}")

    target.parent.mkdir(parents=True, exist_ok=True)
    fn(source, target)  # type: ignore[operator]
    return target
