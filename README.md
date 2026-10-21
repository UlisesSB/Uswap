<p align="center">
  <img src="assets/banner.png" alt="USwap" width="520">
</p>

<p align="center">
  <b>Lightweight, keyboard-driven file converter for your terminal.</b><br>
  Images, audio, video and documents &mdash; 100% offline, no GUI toolkit, no bloat.
</p>

<p align="center">
  <a href="https://github.com/YOUR-USER/uswap/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/YOUR-USER/uswap/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-E11D2E">
  <img alt="Platforms" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-E11D2E">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-E11D2E">
</p>

<p align="center">
  English &middot; <a href="README.es.md">Espa&ntilde;ol</a>
</p>

---

```text
╭─────────────╮
│  █  █ █▀▀▀  │   USwap v0.1.0
│  █  █ ▀▀▀█  │   File conversion engine
│  ▀▄▄▀ █▄▄█  │   ────────────────────────────────
│      ⇄      │   CLI command: uswap
╰─────────────╯
```

## Why USwap?

* **Right-click, pick, done.** A compact pop-up terminal opens from your file manager, you press a number, the file is converted and the window closes.
* **A real TUI when you need it.** Browse folders, batch-convert with progress bars, watch a folder and convert whatever lands in it.
* **Keyboard first.** Arrow keys *and* Vim keys (`j`/`k`, `g`/`G`, `/` to search, `Esc`).
* **Honest about file types.** Detection uses *magic bytes*, not just extensions: a PNG renamed to `.jpg` is still treated as a PNG.
* **Private.** Everything runs locally on top of Pillow, FFmpeg, Pandoc and Poppler.
* **Scriptable.** `uswap photo.heic --to jpg` works without any UI.
* **Clean look.** No emoji; subtle Unicode glyphs (or pure ASCII), and five themes: Gruvbox, Nord, Catppuccin, Tokyo Night, Monokai.

## Install

USwap needs **Python 3.10+**. The recommended way is [pipx](https://pipx.pypa.io/), which keeps it isolated and puts `uswap` on your `PATH`:

```bash
git clone https://github.com/YOUR-USER/uswap.git
cd uswap
pipx install .
```

Or with plain pip: `pip install --user .`

> Once published to PyPI this becomes simply `pipx install uswap`.

### External tools (optional, per format family)

Images work out of the box. Install the rest only for the formats you need:

| Tool | Enables | Debian/Ubuntu | Fedora | Arch | Windows |
|------|---------|---------------|--------|------|---------|
| FFmpeg | audio & video | `sudo apt install ffmpeg` | `sudo dnf install ffmpeg` | `sudo pacman -S ffmpeg` | `winget install Gyan.FFmpeg` |
| Pandoc | documents | `sudo apt install pandoc` | `sudo dnf install pandoc` | `sudo pacman -S pandoc` | `winget install JohnMacFarlane.Pandoc` |
| Poppler | PDF to text/images | `sudo apt install poppler-utils` | `sudo dnf install poppler-utils` | `sudo pacman -S poppler` | `scoop install poppler` |

Run `uswap --doctor` at any time to see what is available.

### Right-click menu integration

**Linux** (Nautilus, Dolphin, Thunar, Nemo):

```bash
./scripts/install.sh            # use --all to force every file manager
./scripts/install.sh --uninstall
```

**Windows** (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Uninstall
```

Details and caveats: [docs/CONTEXT_MENUS.md](docs/CONTEXT_MENUS.md).

## Usage

```text
uswap                     open the dashboard
uswap FILE                quick pop-up for one file
uswap FILE FILE ...       batch mode (pick one target for all)
uswap FILE --to FORMAT    convert without UI (globs and folders allowed)
uswap --watch DIR         convert new files in DIR automatically
uswap --config            settings panel
uswap --doctor            dependency check
uswap --formats           list supported formats
```

Examples:

```bash
uswap song.wav                       # interactive pop-up
uswap "*.png" --to webp -o ./out     # headless, custom output folder
uswap ~/Pictures --to jpg -j 8       # every supported file in a folder, 8 workers
uswap --watch ~/Downloads --rule heic:jpg --rule image:webp
```

### Supported conversions

| From | To |
|------|----|
| Images (PNG, JPG, WebP, GIF, BMP, TIFF, ICO) | PNG, JPG, WebP, BMP, GIF, TIFF, ICO, PDF |
| Audio (MP3, WAV, FLAC, OGG, Opus, AAC, M4A) | MP3, WAV, FLAC, OGG, Opus, AAC, M4A |
| Video (MP4, MKV, WebM, AVI, MOV) | MP4, MKV, WebM, AVI, MOV, GIF, plus audio extraction |
| Documents (MD, TXT, HTML, DOCX, ODT, RTF, EPUB) | MD, TXT, HTML, DOCX, ODT, RTF, EPUB |
| PDF | TXT, PNG, JPG |

### Keys

| Key | Action |
|-----|--------|
| `j` / `k`, arrows | move |
| `g` / `G`, Home / End | first / last |
| `/` | search (Enter keeps the filter, Esc clears it) |
| `Enter` | select / confirm |
| `Space` | toggle (multi-select) |
| `l` / `h` | enter folder / go up (browser) |
| `a`, `*` | select all supported / by wildcard (batch browser) |
| `.` | show hidden files |
| `1`-`9` | quick pick in the pop-up |
| `Esc`, `q` | back / quit |

## Configuration

Stored in `~/.config/uswap/config.json` (Linux) or `%APPDATA%\uswap\config.json` (Windows) and editable from `uswap --config`: language (EN/ES), theme, output folder (same / custom / `~/Downloads`), naming (keep / suffix / overwrite), image quality, workers and watcher rules. See [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Documentation

* [Installation](docs/INSTALLATION.md)
* [Usage guide](docs/USAGE.md)
* [Configuration](docs/CONFIGURATION.md)
* [Context menus](docs/CONTEXT_MENUS.md)
* [Architecture](docs/ARCHITECTURE.md)
* [Development guide](docs/DEVELOPMENT.md)
* [Contributing](CONTRIBUTING.md) &middot; [Changelog](CHANGELOG.md)

## Roadmap

* DOCX/ODT to PDF (via LibreOffice, optional)
* HEIC/AVIF input, animated GIF to video
* Per-format quality presets
* Packaged builds (PyPI, AUR, winget, Scoop)

## Contributing

Issues and pull requests are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

[MIT](LICENSE) &copy; 2026 YOUR NAME

<p align="center"><sub>Made by <a href="https://github.com/YOUR-USER">YOUR NAME</a> &middot; <a href="mailto:you@example.com">you@example.com</a></sub></p>
