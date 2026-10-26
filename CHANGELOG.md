# Changelog

## [2.0.0] - 2026-10-26

A full rewrite focused on being small, simple and easy to install.

### Changed
- USwap is now a single file, `uswap.py`, that uses only the Python standard library.
- Images are converted with FFmpeg (Pillow is no longer needed).
- The terminal interface is drawn with plain ANSI colors (rich is no longer needed).
- The Linux installer uses your distro's packages only: no pip, no virtualenv. This fixes
  installs that hung while downloading dependencies.
- New pixel logo in red, amber and charcoal.
- Converted files always go next to the original and never overwrite anything.

### Added
- Right-click a folder to convert every file of one kind inside it.
- Windows: "Send to › USwap" to convert several files at once.
- Video to GIF with a proper color palette.

### Removed
- Folder watcher, themes, settings panel and Spanish interface (the README stays bilingual).
- Image to PDF (Pandoc and FFmpeg cannot do it without extra tools).

## [0.1.0]

First public version.
