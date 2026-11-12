"""Excepciones del dominio de XFiles."""


class XFilesError(Exception):
    """Error base de la aplicación."""


class ConversionError(XFilesError):
    """Fallo durante una conversión de archivos."""


class PdfOperationError(XFilesError):
    """Fallo durante una operación sobre PDFs (dividir/unir)."""
