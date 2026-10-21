# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added
- Quick pop-up mode (`uswap FILE`) for OS context menus.
- Full TUI dashboard: file browser, batch conversion, hot-folder watcher, settings, dependency check.
- Headless mode: `uswap FILE --to FORMAT` (globs, folders, `-o`, `-j`).
- Magic-byte file type detection (images, audio, video, documents).
- Engines: Pillow (images), FFmpeg (audio/video), Pandoc (documents), Poppler (PDF to text/images).
- Configuration file, EN/ES interface, five color themes (Gruvbox, Nord, Catppuccin, Tokyo Night, Monokai).
- Linux (Nautilus, Dolphin, Thunar, Nemo) and Windows Explorer context-menu installers.
- Red logo assets and a reproducible generator (`scripts/make_assets.py`).
