# XFiles

Aplicación de escritorio **multiplataforma** (Windows y Linux) para transformar
archivos, con instalador propio.

Convierte entre **PDF, Word (.docx), texto plano y Markdown**, y permite
**dividir** y **unir** PDFs.

## Características

| Operación | Descripción |
|-----------|-------------|
| PDF → TXT | Extrae el texto del PDF |
| PDF → Markdown | Extrae texto manteniendo títulos y listas |
| PDF → Word (.docx) | Genera un documento con títulos y párrafos |
| Word → PDF | Alta fidelidad vía LibreOffice/Word (o respaldo de texto plano) |
| Word → TXT / MD | Extrae el contenido del documento |
| TXT → PDF / MD / DOCX | Conversión desde texto plano |
| MD → PDF / TXT / DOCX | Conversión desde Markdown |
| Dividir PDF | Una página por archivo, por rangos (`1-3,5,7-9`) o cada N páginas |
| Unir PDF | Combina varios PDFs respetando el orden |

## Arquitectura

```
src/xfiles/
├── core/          # Motor de conversiones y operaciones PDF (sin GUI)
│   ├── converter.py   # 12 conversiones + despachador por extensión
│   ├── pdf_ops.py     # split / merge
│   └── structure.py   # extracción estructurada de texto desde PDF
├── gui/           # Interfaz gráfica (PySide6 / Qt6)
│   ├── main_window.py # ventana principal con 3 pestañas
│   ├── convert_tab.py # pestaña "Convertir"
│   ├── split_tab.py   # pestaña "Dividir PDF"
│   ├── merge_tab.py   # pestaña "Unir PDFs"
│   └── worker.py      # tareas en segundo plano (QThreadPool)
├── cli.py         # Interfaz de línea de comandos
├── app.py         # Punto de entrada de la GUI
└── resources/     # Iconos
```

El núcleo (`core`) es **independiente de la GUI**, por lo que puede usarse
desde scripts, desde la CLI o desde otra interfaz.

## Desarrollo

Requisitos: Python 3.12 y [Poetry](https://python-poetry.org/).

```bash
poetry install

# Ejecutar la GUI
poetry run xfiles

# Ejecutar tests
poetry run pytest

# CLI
poetry run xfiles-cli convert entrada.pdf salida.md
poetry run xfiles-cli split entrada.pdf salida/ --mode ranges --ranges "1-3,5"
poetry run xfiles-cli merge salida/unido.pdf a.pdf b.pdf c.pdf
```

## Generar instaladores

Los instaladores se construyen automáticamente en GitHub Actions al publicar un
tag `v*` (o manualmente desde la pestaña *Actions*), y producen:

- **Windows**: `XFiles-Setup-0.1.0.exe` (Inno Setup) — descargable como artefacto `XFiles-windows`.
- **Linux**: `xfiles_0.1.0_amd64.deb` + `XFiles-linux-0.1.0.tar.gz` — artefacto `XFiles-linux`.

### Compilar localmente

```bash
# 1) Iconos (requiere Pillow para el .ico de Windows)
poetry run python scripts/make_icons.py

# 2) Ejecutable (carpeta dist/XFiles)
poetry run pyinstaller packaging/XFiles.spec --noconfirm --clean

# 3a) Instalador Linux (.deb) + portable
bash packaging/linux/build_deb.sh

# 3b) Instalador Windows (en una máquina con Windows + Inno Setup)
ISCC.exe packaging\windows\XFiles.iss
```

## Notas

- **PDF escaneado**: si un PDF no tiene texto extraíble (solo imágenes), la
  conversión avisa de que se necesitaría OCR (no incluido en esta versión).
- **Word → PDF**: usa LibreOffice (headless) si está instalado; en Windows
  también usa Microsoft Word; si ninguno está disponible, genera un PDF de
  texto plano como respaldo.
- **`.doc` (Word 97-2003)**: no soportado; guarda el archivo como `.docx`.

## Licencia

Proyecto privado.
