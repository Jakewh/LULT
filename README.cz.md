# LULT - Linux Unreal Localization Tool

LULT je desktopová GUI aplikace pro Linux, která zjednodušuje lokalizační workflow Unreal Engine nad soubory `.pak`, `.locres` a `.csv`.

Hlavní workflow:
1. Rozbalení vybraného `.pak`
2. Export vybraných (nebo všech) `.locres` do editovatelných `.csv`
3. Import upravených `.csv` zpět do `.locres`
4. Přepakování do nového výstupního archivu (`*_P.pak`)

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
