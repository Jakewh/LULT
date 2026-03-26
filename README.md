# LULT - Linux Unreal Localization Tool 🇬🇧

LULT is a desktop GUI application for Linux that simplifies the Unreal Engine localization workflow over `.pak`, `.locres` and `.csv` files using repack and unreallocres.

Main workflow:
1. Unpack a selected `.pak`
2. Export selected (or all) `.locres` files to editable `.csv`
3. Import edited `.csv` back into `.locres`
4. Repack into a new output archive (`*_P.pak`)

<img width="927" height="937" alt="obrazek" src="https://github.com/user-attachments/assets/c70e6f29-5a3d-46e9-b386-2222358305c7" />



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


# LULT - Linux Unreal Localization Tool 🇨🇿

LULT je desktopová GUI aplikace pro Linux, která zjednodušuje lokalizační workflow Unreal Engine nad soubory `.pak`, `.locres` a `.csv` pomocí aplikací repack a unreallocres.

Hlavní workflow:
1. Rozbalení vybraného `.pak`
2. Export vybraných (nebo všech) `.locres` do editovatelných `.csv`
3. Import upravených `.csv` zpět do `.locres`
4. Přepakování do nového výstupního archivu (`*_P.pak`)

<img width="925" height="932" alt="obrazek" src="https://github.com/user-attachments/assets/6aeacbff-011c-4dcb-905f-a06fb867beb9" />


English README: viz [README.md](README.md)

## Funkce

- Jednoduché desktopové rozhraní v PyQt6
- Extrakce jednoho nebo všech `.locres` do `.csv`
- Zpětný import a vytvoření nového paku
- Kontrola a aktualizace runtime nástrojů (repak + UnrealLocres)
- Build AppImage a instalace desktop launcheru pro Linux

## Struktura projektu

- `Lult.py` - hlavní aplikace
- `run.sh` - spuštění ze zdrojového kódu
- `build_single_linux.sh` - build binárky + AppImage
- `install_desktop.sh` - instalace launcheru a desktop záznamu
- `icons/` - ikony aplikace a jazyků
- `repak/` - zdroj repaku a/nebo zkompilovaná binárka
- `unreallocres/UnrealLocres.exe` - pomocná binárka UnrealLocres

## Rychlé spuštění (ze zdroje)

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

Výstupy:
- `dist/LULT`
- `dist/LULT-<arch>.AppImage`

## Instalace desktop launcheru

```bash
./install_desktop.sh
```

## Závislosti

Detailní seznam závislostí (včetně pomocných nástrojů a odkazů) je v [DEPENDENCIES.md](DEPENDENCIES.md).

Klíčové body:
- pro `UnrealLocres.exe` se primárně používá `mono`
- `wine` je jen volitelná fallback varianta (většinou není potřeba, pokud funguje mono)

## Pomocné programy (s odkazy)

- repak: https://github.com/trumank/repak
- UnrealLocres: https://github.com/akintos/UnrealLocres
- PyInstaller: https://pyinstaller.org/
- AppImage tool: https://github.com/AppImage/appimagetool

## Licence

Projekt je licencovaný pod MIT licencí. Viz [LICENSE](LICENSE).
