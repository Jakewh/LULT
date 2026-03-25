# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog:
https://keepachangelog.com/en/1.1.0/

## [Unreleased]

### Added
- Tool health badges in Tool Check footer:
  - green check mark for OK tools
  - orange triangle for available update
  - red exclamation mark for missing or corrupted tools
- Per-tool detail evaluation for `mono`, `repak`, and `UnrealLocres`
- Rich text rendering for status symbols in the footer (better cross-system compatibility)
- GitHub publication bundle in `Git/`:
  - `README.md` (EN)
  - `README.cz.md` (CZ)
  - `DEPENDENCIES.md`
  - `LICENSE`
  - `.gitignore`
  - `CONTRIBUTING.md`

### Changed
- Tool check summary now provides detailed status per tool instead of a single generic message.
- Badge rendering changed from emoji to colored rich-text symbols (`✔`, `▲`, `!`) to avoid missing glyph issues on some Linux setups.

### Fixed
- Missing visual status icons in footer on systems without full emoji font support.
- Install update workflow reliability when replacing an in-use AppImage (deployment process verified with hash parity checks).

## [0.1.0] - 2026-03-25

### Added
- Initial public project packaging and documentation set for GitHub release.
