"""Núcleo de XFiles: conversiones y operaciones sobre PDFs (sin dependencia de la GUI)."""

from .converter import convert, OUTPUT_FORMATS, INPUT_EXTENSIONS
from .pdf_ops import split_pdf, merge_pdfs
from .errors import XFilesError, ConversionError, PdfOperationError

__all__ = [
    "convert",
    "split_pdf",
    "merge_pdfs",
    "OUTPUT_FORMATS",
    "INPUT_EXTENSIONS",
    "XFilesError",
    "ConversionError",
    "PdfOperationError",
]
