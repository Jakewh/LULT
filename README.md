# <img width="64" height="64" alt="icon" src="https://github.com/user-attachments/assets/6bbb4900-9ab0-48fc-9a1c-2d940547c9c4" /> LULT - Linux Unreal Localization Tool 🇬🇧

LULT is a desktop GUI application for Linux that simplifies the Unreal Engine localization workflow over `.pak`, `.locres` and `.csv` files using repack and unreallocres.

Main workflow:
1. Unpack a selected `.pak`, `utoc`, `ucas`
2. Export selected (or all) `.locres` files to editable `.csv`
3. Import edited `.csv` back into `.locres`
4. Repack into a new output archive (`*_P.pak`)

<img width="927" height="937" alt="obrazek" src="https://github.com/user-attachments/assets/c70e6f29-5a3d-46e9-b386-2222358305c7" />

Czech README: see [README.cz.md](README.cz.md)

## Features

- Simple PyQt6 desktop interface
- Single-file or bulk `.locres` extraction to `.csv`
- Re-import workflow with output pak generation
- Runtime tool check and refresh (repak + retoc + UnrealLocres)
- Linux AppImage build and desktop launcher install scripts

## Helper Programs (with links)

- repak: https://github.com/trumank/repak
- retoc : https://github.com/trumank/retoc
- UnrealLocres: https://github.com/akintos/UnrealLocres
- PyInstaller: https://pyinstaller.org/
- AppImage tool: https://github.com/AppImage/appimagetool

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).



##

# <img width="64" height="64" alt="icon" src="https://github.com/user-attachments/assets/6bbb4900-9ab0-48fc-9a1c-2d940547c9c4" /> LULT - Linux Unreal Localization Tool 🇨🇿

LULT je desktopová GUI aplikace pro Linux, která zjednodušuje lokalizační workflow Unreal Engine nad soubory `.pak`, `.locres` a `.csv` pomocí aplikací repack a unreallocres.

Hlavní workflow:
1. Rozbalení vybraného `.pak`, `utoc`, `ucas`
2. Export vybraných (nebo všech) `.locres` do editovatelných `.csv`
3. Import upravených `.csv` zpět do `.locres`
4. Přepakování do nového výstupního archivu (`*_P.pak`)

<img width="925" height="932" alt="obrazek" src="https://github.com/user-attachments/assets/6aeacbff-011c-4dcb-905f-a06fb867beb9" />


English README: viz [README.md](README.md)

## Funkce

- Jednoduché desktopové rozhraní v PyQt6
- Extrakce jednoho nebo všech `.locres` do `.csv`
- Zpětný import a vytvoření nového paku
- Kontrola a aktualizace runtime nástrojů (repak + retoc + UnrealLocres)
- Build AppImage a instalace desktop launcheru pro Linux

## Pomocné programy (s odkazy)

- repak: https://github.com/trumank/repak
- retoc : https://github.com/trumank/retoc
- UnrealLocres: https://github.com/akintos/UnrealLocres
- PyInstaller: https://pyinstaller.org/
- AppImage tool: https://github.com/AppImage/appimagetool

## Licence

Projekt je licencovaný pod MIT licencí. Viz [LICENSE](LICENSE).
