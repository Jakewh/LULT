# LULT - Linux Unreal Localization Tool

LULT is a desktop GUI app for Linux that simplifies Unreal Engine localization workflows around `.pak`, `.locres`, and `.csv` files.

Main workflow:
1. Unpack a selected `.pak`
2. Export selected (or all) `.locres` files to editable `.csv`
3. Import edited `.csv` back into `.locres`
4. Repack into a new output archive (`*_P.pak`)

Czech README: see [README.cz.md](README.cz.md)

## Features

- Simple PyQt6 desktop interface
- Single-file or bulk `.locres` extraction to `.csv`
- Re-import workflow with output pak generation
- Runtime tool check and refresh (repak + UnrealLocres)
- Linux AppImage build and desktop launcher install scripts

## Project Structure

- `Lult.py` - main application
- `run.sh` - run from source
- `build_single_linux.sh` - build binary + AppImage
- `install_desktop.sh` - install launcher and desktop entry
- `icons/` - app and language icons
- `repak/` - repak source and/or built binary
- `unreallocres/UnrealLocres.exe` - UnrealLocres helper binary

## Quick Start (Source)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

## Build AppImage

```bash
./build_single_linux.sh
```

Outputs:
- `dist/LULT`
- `dist/LULT-<arch>.AppImage`

## Install Desktop Launcher

```bash
./install_desktop.sh
```

## Dependencies

Detailed dependency list (including helper tools and links) is available in [DEPENDENCIES.md](DEPENDENCIES.md).

Key points:
- `mono` is the primary runtime for `UnrealLocres.exe`
- `wine` is optional fallback only (usually not needed when mono works)

## Helper Programs (with links)

- repak: https://github.com/trumank/repak
- UnrealLocres: https://github.com/akintos/UnrealLocres
- PyInstaller: https://pyinstaller.org/
- AppImage tool: https://github.com/AppImage/appimagetool

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
