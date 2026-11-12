"""Interfaz de línea de comandos de XFiles (útil para scripting y pruebas)."""

from __future__ import annotations

import argparse
import sys

from xfiles import __version__
from xfiles.core import ConversionError, PdfOperationError, XFilesError
from xfiles.core.converter import convert
from xfiles.core.pdf_ops import merge_pdfs, split_pdf


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xfiles-cli",
        description="Convierte archivos (PDF/DOCX/TXT/MD) y divide o une PDFs.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    conv = sub.add_parser("convert", help="Convierte un archivo a otro formato")
    conv.add_argument("src", help="Archivo de origen")
    conv.add_argument("dst", help="Archivo de destino (el formato se deduce de la extensión)")

    split = sub.add_parser("split", help="Divide un PDF")
    split.add_argument("src", help="PDF de origen")
    split.add_argument("out_dir", help="Directorio de salida")
    split.add_argument(
        "--mode", choices=["single", "ranges", "every"], default="single",
        help="single: una página por archivo; ranges: por rangos; every: cada N páginas",
    )
    split.add_argument("--ranges", help="Rangos, p. ej. '1-3,5,7-9' (con --mode ranges)")
    split.add_argument("--every", type=int, help="Número de páginas por archivo (con --mode every)")

    merge = sub.add_parser("merge", help="Une varios PDFs")
    merge.add_argument("dst", help="PDF de salida")
    merge.add_argument("srcs", nargs="+", help="PDFs a unir, en orden")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "convert":
            out = convert(args.src, args.dst)
            print(f"Convertido: {out}")
        elif args.cmd == "split":
            produced = split_pdf(
                args.src, args.out_dir, mode=args.mode, ranges=args.ranges, every=args.every
            )
            print(f"Generados {len(produced)} archivos en {args.out_dir}:")
            for path in produced:
                print(f"  - {path}")
        elif args.cmd == "merge":
            out = merge_pdfs(args.srcs, args.dst)
            print(f"Unido en: {out}")
    except (XFilesError, ConversionError, PdfOperationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
