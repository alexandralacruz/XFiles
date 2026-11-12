"""Ventana principal de XFiles."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from xfiles import __version__
from xfiles.gui.convert_tab import ConvertTab
from xfiles.gui.merge_tab import MergeTab
from xfiles.gui.split_tab import SplitTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"XFiles — transformación de archivos (v{__version__})")
        self.resize(680, 560)
        self.setAcceptDrops(True)

        self.tabs = QTabWidget()
        self.convert_tab = ConvertTab()
        self.split_tab = SplitTab()
        self.merge_tab = MergeTab()
        self.tabs.addTab(self.convert_tab, "Convertir")
        self.tabs.addTab(self.split_tab, "Dividir PDF")
        self.tabs.addTab(self.merge_tab, "Unir PDFs")
        self.setCentralWidget(self.tabs)

        self._build_menu()
        self.statusBar().showMessage("Arrastra archivos a la ventana para empezar.")

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&Archivo")
        quit_action = QAction("Salir", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self.menuBar().addMenu("Ay&uda")
        about_action = QAction("Acerca de XFiles", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "Acerca de XFiles",
            f"<b>XFiles</b> v{__version__}<br><br>"
            "Convierte archivos entre PDF, Word, texto plano y Markdown, "
            "y divide o une PDFs.<br><br>"
            "Multiplataforma (Windows y Linux).",
        )

    # ------------------------------------------------------------- #
    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            current = self.tabs.currentWidget()
            if hasattr(current, "accept_paths"):
                current.accept_paths(paths)
            self.statusBar().showMessage(
                f"{len(paths)} archivo(s) añadido(s) a «{self.tabs.tabText(self.tabs.currentIndex())}»."
            )
            event.acceptProposedAction()
