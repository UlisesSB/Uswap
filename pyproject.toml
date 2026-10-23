# Installation

## Quick install

| System | Command |
|--------|---------|
| Windows (installer) | download `USwap-Setup.exe` from the Releases page and run it |
| Windows (source) | `powershell -ExecutionPolicy Bypass -File install.ps1` |
| Linux | `./install.sh` |

Both scripts install the dependencies, the `uswap` command and the right-click entry. Flags: Linux `-y`, `--no-system-deps`, `--no-menus`, `--uninstall`; Windows `-NoSystemDeps`, `-NoMenu`, `-Uninstall`.

What the scripts do:

* **Linux** - installs FFmpeg/Pandoc/Poppler via apt, dnf, pacman or zypper (asks before `sudo`), creates a virtualenv in `~/.local/share/uswap/venv`, links `~/.local/bin/uswap`, then runs `scripts/menu-linux.sh`.
* **Windows** - installs Python 3.12 with winget if needed, creates a virtualenv in `%LOCALAPPDATA%\uswap\venv`, adds `%LOCALAPPDATA%\uswap\bin` to your user PATH, installs the tools with winget, then runs `scripts\menu-windows.ps1`. Open a new terminal afterwards so PATH changes apply.
* **USwap-Setup.exe** - a self-contained Inno Setup installer built by the release workflow. It ships `uswap.exe` (PyInstaller) with FFmpeg, Pandoc and Poppler in `tools\`, so no Python is needed. Per-user install, optional PATH and right-click tasks.

The rest of this page covers manual installation.

## Requirements

* Python **3.10 or newer** (Windows or Linux)
* A terminal with Unicode support (any modern one). For legacy terminals set *Settings > Symbols > ASCII only*.

## Install USwap

### With pipx (recommended)

```bash
git clone https://github.com/UlisesSB/uswap.git
cd uswap
pipx install .
uswap --version
```

Upgrade after pulling changes: `pipx install --force .`

### With pip

```bash
pip install --user .
```

Make sure the scripts directory is on your `PATH` (`~/.local/bin` on Linux, `%APPDATA%\Python\Python3xx\Scripts` on Windows).

### From a virtual environment (development)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## External tools

USwap shells out to well-known tools. All are optional; a missing tool only disables the formats that need it.

| Tool | Needed for | Binary names |
|------|-----------|--------------|
| FFmpeg | audio, video | `ffmpeg`, `ffprobe` |
| Pandoc | MD, TXT, HTML, DOCX, ODT, RTF, EPUB | `pandoc` |
| Poppler | PDF to TXT / PNG / JPG | `pdftotext`, `pdftoppm` |

Install commands per platform are in the [README](../README.md#external-tools-optional-per-format-family). Check the result with:

```bash
uswap --doctor
```

## Context menus

See [CONTEXT_MENUS.md](CONTEXT_MENUS.md).

## Uninstall

```bash
./install.sh --uninstall              # Linux: program, venv and menu entries
```

Windows: *Settings > Apps > USwap* (installer) or `install.ps1 -Uninstall`. Manual installs: `pipx uninstall uswap`. Your settings file is left in place; delete the `uswap` config folder to remove it.
