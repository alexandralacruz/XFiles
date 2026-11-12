"""Pestaña para unir PDFs."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from xfiles.core import merge_pdfs
from xfiles.gui.worker import run_in_background
from xfiles.gui.widgets import FileField, open_in_file_manager


class MergeTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("PDFs a unir (el orden importa):"))
        self.list = QListWidget()
        self.list.setMinimumHeight(140)
        layout.addWidget(self.list)

        buttons = QHBoxLayout()
        add_btn = QPushButton("Añadir…")
        remove_btn = QPushButton("Quitar")
        up_btn = QPushButton("Subir")
        down_btn = QPushButton("Bajar")
        add_btn.clicked.connect(self._add)
        remove_btn.clicked.connect(self._remove)
        up_btn.clicked.connect(lambda: self._move(-1))
        down_btn.clicked.connect(lambda: self._move(1))
        for b in (add_btn, remove_btn, up_btn, down_btn):
            buttons.addWidget(b)
        layout.addLayout(buttons)

        layout.addWidget(QLabel("PDF de salida:"))
        self.output = FileField(mode="save", filter="PDF (*.pdf)")
        layout.addWidget(self.output)

        self.merge_btn = QPushButton("Unir PDFs")
        self.merge_btn.clicked.connect(self._merge)
        layout.addWidget(self.merge_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.status = QLabel("Listo")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        layout.addStretch(1)

    def _add(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Añadir PDFs", "", "PDF (*.pdf)")
        for path in paths:
            if path not in self._paths():
                self.list.addItem(path)

    def _remove(self) -> None:
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))

    def _move(self, delta: int) -> None:
        row = self.list.currentRow()
        target = row + delta
        if 0 <= row < self.list.count() and 0 <= target < self.list.count():
            item = self.list.takeItem(row)
            self.list.insertItem(target, item)
            self.list.setCurrentRow(target)

    def _paths(self) -> list[str]:
        return [self.list.item(i).text() for i in range(self.list.count())]

    def _merge(self) -> None:
        paths = self._paths()
        dst = self.output.path()
        if not paths:
            QMessageBox.warning(self, "XFiles", "Añade al menos un PDF.")
            return
        if not dst:
            QMessageBox.warning(self, "XFiles", "Indica un archivo de salida.")
            return

        self._set_busy(True)
        worker = run_in_background(merge_pdfs, paths, dst)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)

    def _on_finished(self, result: object) -> None:
        self._set_busy(False)
        out = str(result)
        self.status.setText(f"✔ PDF unido: {out}")
        box = QMessageBox(self)
        box.setWindowTitle("XFiles")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText("PDFs unidos correctamente.")
        box.setInformativeText(out)
        open_btn = box.addButton("Abrir carpeta", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            open_in_file_manager(out)

    def _on_error(self, message: str) -> None:
        self._set_busy(False)
        self.status.setText(f"✖ Error: {message}")
        QMessageBox.critical(self, "XFiles", f"Error al unir:\n{message}")

    def _set_busy(self, busy: bool) -> None:
        self.merge_btn.setEnabled(not busy)
        self.progress.setVisible(busy)

    def accept_paths(self, paths: list[str]) -> None:
        for path in paths:
            if path not in self._paths():
                self.list.addItem(path)
