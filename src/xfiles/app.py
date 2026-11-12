"""Punto de entrada de la aplicación de escritorio XFiles."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from xfiles.gui.main_window import MainWindow
from xfiles.resources import resource_path


def main() -> int:
    if "--selftest" in sys.argv:
        from xfiles.selftest import run

        return run()

    app = QApplication(sys.argv)
    app.setApplicationName("XFiles")
    app.setApplicationDisplayName("XFiles")
    app.setOrganizationName("XFiles")

    for name in ("xfiles.png", "xfiles.svg"):
        icon = resource_path(name)
        if icon.exists():
            app.setWindowIcon(QIcon(str(icon)))
            break

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
