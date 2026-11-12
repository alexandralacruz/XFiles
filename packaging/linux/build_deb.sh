#!/usr/bin/env bash
# Empaqueta XFiles como .deb (instalador Debian/Ubuntu) y .tar.gz (portable).
# Requiere haber generado antes el build de PyInstaller (dist/XFiles).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
APP="XFiles"
VERSION="0.1.0"
DIST="$ROOT/dist/$APP"
OUT="$ROOT/packaging/dist"
PKGROOT="$ROOT/packaging/build/deb"

if [ ! -d "$DIST" ]; then
  echo "No se encontró $DIST."
  echo "Ejecuta primero: poetry run pyinstaller packaging/XFiles.spec --noconfirm --clean"
  exit 1
fi

rm -rf "$PKGROOT" "$OUT"
mkdir -p "$PKGROOT/DEBIAN" "$PKGROOT/usr/lib/xfiles" "$PKGROOT/usr/bin" \
         "$PKGROOT/usr/share/applications" \
         "$PKGROOT/usr/share/icons/hicolor/256x256/apps" "$OUT"

cp -a "$DIST/." "$PKGROOT/usr/lib/xfiles/"

cat > "$PKGROOT/DEBIAN/control" <<EOF
Package: xfiles
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Alexandra La Cruz <alexandra.lacruz@gmail.com>
Depends: libc6, libpango-1.0-0, libpangoft2-1.0-0, libharfbuzz0b, libglib2.0-0, libgobject-2.0-0, libgdk-pixbuf-2.0-0, libfontconfig1
Description: Convierte archivos (PDF/DOCX/TXT/Markdown) y divide/une PDFs.
 Aplicación de escritorio multiplataforma para transformar archivos:
 convertir PDF a Word/texto/Markdown (y viceversa), dividir y unir PDFs.
EOF

cat > "$PKGROOT/usr/bin/xfiles" <<'EOF'
#!/bin/sh
exec /usr/lib/xfiles/XFiles "$@"
EOF
chmod +x "$PKGROOT/usr/bin/xfiles"

cp "$ROOT/src/xfiles/resources/xfiles.png" \
   "$PKGROOT/usr/share/icons/hicolor/256x256/apps/xfiles.png"

cat > "$PKGROOT/usr/share/applications/xfiles.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=XFiles
Comment=Convierte archivos y divide/une PDFs
Exec=xfiles
Icon=xfiles
Terminal=false
Categories=Utility;Office;
EOF

dpkg-deb --build --root-owner-group "$PKGROOT" "$OUT/xfiles_${VERSION}_amd64.deb"
tar -C "$ROOT/dist" -czf "$OUT/XFiles-linux-${VERSION}.tar.gz" "$APP"

echo "✔ Generado: $OUT/xfiles_${VERSION}_amd64.deb"
echo "✔ Generado: $OUT/XFiles-linux-${VERSION}.tar.gz"
