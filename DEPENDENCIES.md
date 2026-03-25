# Dependencies

This document lists runtime/build dependencies and helper programs required to use, build, and publish LULT.

## Runtime Dependencies (Linux)

- Python 3.10+ (for source run)
  - https://www.python.org/
- PyQt6 (GUI)
  - https://pypi.org/project/PyQt6/
- mono (required to run `UnrealLocres.exe` in this project)
  - https://www.mono-project.com/

## Tooling Dependencies

- repak (pak unpack/pack)
  - https://github.com/trumank/repak
- UnrealLocres (`.locres` import/export helper)
  - https://github.com/akintos/UnrealLocres

## Build Dependencies

- pip / setuptools / wheel
  - https://pypi.org/project/pip/
  - https://pypi.org/project/setuptools/
  - https://pypi.org/project/wheel/
- PyInstaller (Linux executable bundling)
  - https://pyinstaller.org/
- appimagetool (AppImage packaging)
  - https://github.com/AppImage/appimagetool
- curl or wget (used by build script to download appimagetool when missing)
  - https://curl.se/
  - https://www.gnu.org/software/wget/

## Optional Dependencies

- Rust + Cargo (only needed if repak binary is missing and must be built from source)
  - https://www.rust-lang.org/
- Wine (optional fallback for `.exe` execution)
  - https://www.winehq.org/

## Notes About `.exe` Support

- In this project, `UnrealLocres.exe` is intended to run through `mono`.
- `wine` is not required in normal setup.
- If you encounter edge-case compatibility issues with mono, wine can be tested as fallback.

## Quick Install (Fedora example)

```bash
sudo dnf install -y python3 python3-pip mono-complete curl
```

Optional:

```bash
sudo dnf install -y wine cargo rust
```
