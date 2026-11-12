"""Widgets auxiliares reutilizables."""

from __future__ import annotations

import os

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FileField(QWidget):
    """Campo de texto con botón para elegir archivo/carpeta."""

    path_changed = Signal(str)

    def __init__(
        self,
        mode: str = "open",
        filter: str = "Todos los archivos (*)",
        placeholder: str = "Selecciona un archivo...",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.mode = mode
        self.filter = filter

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.textChanged.connect(self._on_text_changed)
        button = QPushButton("Examinar…")
        button.clicked.connect(self._browse)
        layout.addWidget(self.edit, 1)
        layout.addWidget(button)

    def _on_text_changed(self, text: str) -> None:
        self.path_changed.emit(text.strip())

    def _browse(self) -> None:
        if self.mode == "dir":
            path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        elif self.mode == "save":
            path, _ = QFileDialog.getSaveFileName(
                self, "Guardar como", self.edit.text(), self.filter
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Abrir archivo", self.edit.text(), self.filter
            )
        if path:
            self.set_path(path)

    def set_path(self, path: str) -> None:
        self.edit.setText(path)

    def path(self) -> str:
        return self.edit.text().strip()


def open_in_file_manager(path: str) -> None:
    """Abre el administrador de archivos en la carpeta de `path`."""
    target = os.path.dirname(path) if os.path.isfile(path) else path
    QDesktopServices.openUrl(QUrl.fromLocalFile(target))
