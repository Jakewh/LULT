#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APPIMAGE_SRC="$ROOT_DIR/dist/LULT-$(uname -m).AppImage"
ICON_SRC="$ROOT_DIR/icons/lult_app.svg"

if [[ ! -f "$APPIMAGE_SRC" ]]; then
  echo "ERROR: AppImage not found: $APPIMAGE_SRC" >&2
  echo "Run ./build_single_linux.sh first." >&2
  exit 1
fi

if [[ ! -f "$ICON_SRC" ]]; then
  echo "ERROR: Icon not found: $ICON_SRC" >&2
  exit 1
fi

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$BIN_DIR" "$APP_DIR" "$ICON_DIR"

APPIMAGE_DST="$BIN_DIR/LULT.AppImage"
LAUNCHER_DST="$BIN_DIR/lult"
DESKTOP_DST="$APP_DIR/lult.desktop"
ICON_DST="$ICON_DIR/lult_app.svg"

cp "$APPIMAGE_SRC" "$APPIMAGE_DST"
chmod +x "$APPIMAGE_DST"
cp "$ICON_SRC" "$ICON_DST"

cat > "$LAUNCHER_DST" << EOF
#!/usr/bin/env bash
set -euo pipefail
exec env APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGE_DST" "\$@"
EOF
chmod +x "$LAUNCHER_DST"

cat > "$DESKTOP_DST" << EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=LULT
Comment=Linux Unreal Localization Tool
Exec=$LAUNCHER_DST
Icon=lult_app
Terminal=false
Categories=Utility;Development;
StartupNotify=true
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Installed: $DESKTOP_DST"
echo "Launcher: $LAUNCHER_DST"
echo "AppImage: $APPIMAGE_DST"
