"""Genera los iconos (PNG/ICO) a partir del SVG fuente.

Uso:  poetry run python scripts/make_icons.py
Requiere PySide6 (QSvgRenderer) y Pillow (para el .ico).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "src" / "xfiles" / "resources" / "xfiles.svg"
OUT = ROOT / "src" / "xfiles" / "resources"


def render_png(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    # Fondo negro, igual que el fondo del logo, para que el letterboxing
    # (KeepAspectRatio) sea invisible y no se deforme el diseño.
    image.fill(Qt.GlobalColor.black)
    painter = QPainter(image)
    renderer = QSvgRenderer(str(SVG))
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return image


def main() -> None:
    sizes = (16, 32, 48, 64, 128, 256)
    for size in sizes:
        render_png(size).save(str(OUT / f"xfiles-{size}.png"))
    render_png(256).save(str(OUT / "xfiles.png"))

    try:
        from PIL import Image

        images = [Image.open(str(OUT / f"xfiles-{s}.png")) for s in sizes]
        images[-1].save(
            str(OUT / "xfiles.ico"),
            format="ICO",
            sizes=[(s, s) for s in sizes],
            append_images=images[:-1],
        )
        print("ICO generado:", OUT / "xfiles.ico")
    except ImportError:
        print("Pillow no disponible: no se generó el .ico (necesario para Windows).")

    print("Iconos PNG generados en:", OUT)


if __name__ == "__main__":
    main()
