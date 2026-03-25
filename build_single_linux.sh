#!/usr/bin/env bash
set -euo pipefail

# Build one distributable Linux binary for LULT.
# Outputs:
# - dist/LULT
# - dist/LULT-<arch>.AppImage

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -f "Lult.py" ]]; then
  echo "ERROR: Lult.py not found in $ROOT_DIR" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required for build." >&2
  exit 1
fi

if [[ ! -f "unreallocres/UnrealLocres.exe" ]]; then
  echo "ERROR: unreallocres/UnrealLocres.exe is missing." >&2
  exit 1
fi

if [[ ! -x "repak/target/release/repak" ]]; then
  if command -v cargo >/dev/null 2>&1 && [[ -f "repak/Cargo.toml" ]]; then
    echo "repak binary not found, building with cargo..."
    (cd repak && cargo build --release)
  else
    echo "ERROR: repak binary missing and cargo build is not available." >&2
    exit 1
  fi
fi

# Isolated build environment.
BUILD_VENV=".venv-build"
python3 -m venv "$BUILD_VENV"
# shellcheck disable=SC1091
source "$BUILD_VENV/bin/activate"

python -m pip install --upgrade pip setuptools wheel >/dev/null
python -m pip install --upgrade pyinstaller PyQt6 >/dev/null

pyinstaller \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --name LULT \
  --add-data "icons:icons" \
  --add-data "unreallocres:unreallocres" \
  --add-data "repak:repak" \
  Lult.py

chmod +x dist/LULT

APPDIR="$ROOT_DIR/build/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"

cp "dist/LULT" "$APPDIR/usr/bin/LULT"
cp "icons/lult_app.svg" "$APPDIR/lult_app.svg"
cp "icons/lult_app.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/lult_app.svg"

cat > "$APPDIR/AppRun" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "$HERE/usr/bin/LULT" "$@"
EOF
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/LULT.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=LULT
Comment=Linux Unreal Localization Tool
Exec=LULT
Icon=lult_app
Categories=Utility;
Terminal=false
EOF

ln -sf "lult_app.svg" "$APPDIR/.DirIcon"

APPIMAGETOOL_CMD=""
if command -v appimagetool >/dev/null 2>&1; then
  APPIMAGETOOL_CMD="$(command -v appimagetool)"
else
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64)
      APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
      ;;
    aarch64)
      APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-aarch64.AppImage"
      ;;
    *)
      echo "ERROR: Unsupported architecture for auto-download: $ARCH" >&2
      exit 1
      ;;
  esac

  APPIMAGETOOL_LOCAL="$ROOT_DIR/.appimagetool.AppImage"
  if [[ ! -x "$APPIMAGETOOL_LOCAL" ]]; then
    if command -v curl >/dev/null 2>&1; then
      curl -L "$APPIMAGETOOL_URL" -o "$APPIMAGETOOL_LOCAL"
    elif command -v wget >/dev/null 2>&1; then
      wget -O "$APPIMAGETOOL_LOCAL" "$APPIMAGETOOL_URL"
    else
      echo "ERROR: Need curl or wget to download appimagetool." >&2
      exit 1
    fi
    chmod +x "$APPIMAGETOOL_LOCAL"
  fi
  APPIMAGETOOL_CMD="$APPIMAGETOOL_LOCAL"
fi

ARCH_TAG="$(uname -m)"
APPIMAGE_OUT="$ROOT_DIR/dist/LULT-$ARCH_TAG.AppImage"
rm -f "$APPIMAGE_OUT"

# APPIMAGE_EXTRACT_AND_RUN avoids FUSE requirement on systems without it.
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL_CMD" "$APPDIR" "$APPIMAGE_OUT"
chmod +x "$APPIMAGE_OUT"

echo
echo "Build complete. Distributable file: $ROOT_DIR/dist/LULT"
echo "Build complete. AppImage: $APPIMAGE_OUT"
echo "Tip: Build on the oldest target distro you need for best compatibility."
