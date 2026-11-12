"""Resolución de rutas de recursos (funciona también dentro de PyInstaller)."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(name: str) -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / name
    return Path(__file__).resolve().parent / "resources" / name
