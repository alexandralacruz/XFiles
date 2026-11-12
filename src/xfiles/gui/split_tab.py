"""Pestaña para dividir PDFs."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from xfiles.core import split_pdf
from xfiles.gui.worker import run_in_background
from xfiles.gui.widgets import FileField, open_in_file_manager

_MODES = [
    ("single", "Una página por archivo"),
    ("ranges", "Por rangos de páginas (ej. 1-3, 5, 7-9)"),
    ("every", "Cada N páginas"),
]


class SplitTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("PDF de origen:"))
        self.source = FileField(mode="open", filter="PDF (*.pdf)")
        layout.addWidget(self.source)

        layout.addWidget(QLabel("Modo de división:"))
        self.mode = QComboBox()
        for key, label in _MODES:
            self.mode.addItem(label, key)
        self.mode.currentIndexChanged.connect(self._on_mode_changed)
        layout.addWidget(self.mode)

        layout.addWidget(QLabel("Rangos de páginas:"))
        self.ranges = QLineEdit()
        self.ranges.setPlaceholderText("Ejemplo: 1-3, 5, 7-9")
        layout.addWidget(self.ranges)

        layout.addWidget(QLabel("Páginas por archivo:"))
        self.every = QSpinBox()
        self.every.setRange(1, 100000)
        self.every.setValue(2)
        layout.addWidget(self.every)

        layout.addWidget(QLabel("Carpeta de destino:"))
        self.out_dir = FileField(mode="dir")
        layout.addWidget(self.out_dir)

        self.split_btn = QPushButton("Dividir PDF")
        self.split_btn.clicked.connect(self._split)
        layout.addWidget(self.split_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.status = QLabel("Listo")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        layout.addStretch(1)
        self._on_mode_changed()

    def _on_mode_changed(self) -> None:
        mode = self.mode.currentData()
        self.ranges.setEnabled(mode == "ranges")
        self.every.setEnabled(mode == "every")

    def _split(self) -> None:
        src = self.source.path()
        out = self.out_dir.path()
        if not src:
            QMessageBox.warning(self, "XFiles", "Selecciona un PDF de origen.")
            return
        if not out:
            QMessageBox.warning(self, "XFiles", "Selecciona una carpeta de destino.")
            return

        mode = self.mode.currentData()
        kwargs = {"mode": mode}
        if mode == "ranges":
            kwargs["ranges"] = self.ranges.text().strip()
        elif mode == "every":
            kwargs["every"] = self.every.value()

        self._set_busy(True)
        worker = run_in_background(split_pdf, src, out, **kwargs)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)

    def _on_finished(self, result: object) -> None:
        self._set_busy(False)
        files = list(result)
        self.status.setText(f"✔ Generados {len(files)} archivos.")
        box = QMessageBox(self)
        box.setWindowTitle("XFiles")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(f"Se generaron {len(files)} archivos en:")
        box.setInformativeText(self.out_dir.path())
        open_btn = box.addButton("Abrir carpeta", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            open_in_file_manager(self.out_dir.path())

    def _on_error(self, message: str) -> None:
        self._set_busy(False)
        self.status.setText(f"✖ Error: {message}")
        QMessageBox.critical(self, "XFiles", f"Error al dividir:\n{message}")

    def _set_busy(self, busy: bool) -> None:
        self.split_btn.setEnabled(not busy)
        self.progress.setVisible(busy)

    def accept_paths(self, paths: list[str]) -> None:
        if paths:
            self.source.set_path(paths[0])
