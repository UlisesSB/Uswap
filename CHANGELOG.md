# Changelog

## [2.1.0] - 2026-10-28

### Added
- **Image to PDF**, built in with no extra tools: one PDF per image, or several images in
  a single PDF (menu, or `uswap *.jpg --to pdf --merge`). Pages fit A4.
- **Optional formats** (add-ons) in the menu, installed only if you want them:
  Documents (Pandoc), PDF reader (Poppler), Documents to PDF (Typst),
  Extra images: HEIC, AVIF, SVG (ImageMagick), Office to PDF (LibreOffice).
  Also from the terminal: `uswap --install NAME`.
- More formats that FFmpeg already reads: wma, aiff, amr, wmv, flv, 3gp, mpeg, ts.
- Office files in: doc, xlsx, xls, ods, pptx, ppt, odp (to PDF, with LibreOffice).
- New-version notice: a small `▲ vX.Y.Z available` line in the menu, checked at most
  once a day. Turn it off with `USWAP_NO_UPDATE_CHECK=1`.
- `uswap --update`: updates only after you confirm (Windows: runs the new installer;
  Linux: `git pull` + `install.sh`).
- When a file needs an add-on you don't have, USwap tells you which one.

### Changed
- The base install only needs Python and FFmpeg. Pandoc and Poppler are now optional,
  which fixes installs that hung downloading Pandoc on Arch-based distros (CachyOS,
  Manjaro...). On Linux, Pandoc and Typst are downloaded as official static builds.
- The Windows installer only bundles FFmpeg, so it is much smaller.
- `uswap --doctor` shows the right install command for your distro, not always `apt`.
- Right-click menus on Linux call `uswap --terminal` (the separate launcher script is gone).

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
