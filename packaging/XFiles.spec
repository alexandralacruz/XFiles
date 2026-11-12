# -*- mode: python ; coding: utf-8 -*-
"""Configuración de PyInstaller para XFiles (build one-folder)."""

import os

from PyInstaller.utils.hooks import collect_all

# Paquetes con datos/binarios dinámicos que hay que recolectar explícitamente.
datas = []
binaries = []
hiddenimports = []
for pkg in ("pymupdf", "weasyprint", "xhtml2pdf", "reportlab", "docx", "fpdf", "markdown"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Recursos propios (iconos).
datas += [("../src/xfiles/resources", "xfiles/resources")]

_ico = "../src/xfiles/resources/xfiles.ico"
icon = _ico if os.path.exists(_ico) else None

a = Analysis(
    ["launcher.py"],
    pathex=["../src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="XFiles",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="XFiles",
)
