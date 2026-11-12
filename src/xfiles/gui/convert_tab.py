"""Pestaña de conversión de archivos."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from xfiles.core import convert
from xfiles.core.converter import OUTPUT_FORMATS
from xfiles.gui.worker import run_in_background
from xfiles.gui.widgets import FileField, open_in_file_manager

_EXT = {"pdf": ".pdf", "docx": ".docx", "txt": ".txt", "md": ".md"}


class ConvertTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Archivo de origen:"))
        self.source = FileField(
            mode="open",
            filter="Documentos soportados (*.pdf *.docx *.txt *.md *.markdown);;PDF (*.pdf);;Word (*.docx);;Texto (*.txt);;Markdown (*.md *.markdown)",
        )
        self.source.path_changed.connect(self._on_source_changed)
        layout.addWidget(self.source)

        layout.addWidget(QLabel("Convertir a:"))
        self.format = QComboBox()
        for key, label in OUTPUT_FORMATS.items():
            self.format.addItem(label, key)
        self.format.currentIndexChanged.connect(self._on_format_changed)
        layout.addWidget(self.format)

        layout.addWidget(QLabel("Archivo de destino:"))
        self.target = FileField(mode="save", filter="Todos los archivos (*)")
        layout.addWidget(self.target)

        self.convert_btn = QPushButton("Convertir")
        self.convert_btn.clicked.connect(self._convert)
        layout.addWidget(self.convert_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.status = QLabel("Listo")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        layout.addStretch(1)

    # ------------------------------------------------------------- #
    def _selected_fmt(self) -> str:
        return self.format.currentData()

    def _suggest_target(self) -> None:
        src = self.source.path()
        if not src:
            return
        stem = Path(src).stem
        directory = Path(src).parent
        ext = _EXT.get(self._selected_fmt(), ".txt")
        self.target.set_path(str(directory / (stem + ext)))

    def _on_source_changed(self, _path: str) -> None:
        self._suggest_target()

    def _on_format_changed(self, _index: int) -> None:
        current = self.target.path()
        if current:
            self.target.set_path(str(Path(current).with_suffix(_EXT[self._selected_fmt()])))
        else:
            self._suggest_target()

    # ------------------------------------------------------------- #
    def _convert(self) -> None:
        src = self.source.path()
        dst = self.target.path()
        if not src:
            QMessageBox.warning(self, "XFiles", "Selecciona un archivo de origen.")
            return
        if not dst:
            QMessageBox.warning(self, "XFiles", "Indica un archivo de destino.")
            return

        self._set_busy(True)
        worker = run_in_background(convert, src, dst)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)

    def _on_finished(self, result: object) -> None:
        self._set_busy(False)
        out = Path(str(result))
        self.status.setText(f"✔ Convertido a: {out}")
        box = QMessageBox(self)
        box.setWindowTitle("XFiles")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText("Conversión completada.")
        box.setInformativeText(str(out))
        open_btn = box.addButton("Abrir carpeta", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            open_in_file_manager(str(out))

    def _on_error(self, message: str) -> None:
        self._set_busy(False)
        self.status.setText(f"✖ Error: {message}")
        QMessageBox.critical(self, "XFiles", f"Error durante la conversión:\n{message}")

    def _set_busy(self, busy: bool) -> None:
        self.convert_btn.setEnabled(not busy)
        self.progress.setVisible(busy)

    # ------------------------------------------------------------- #
    def accept_paths(self, paths: list[str]) -> None:
        if paths:
            self.source.set_path(paths[0])
