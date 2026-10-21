# Installation

## Requirements

* Python **3.10 or newer** (Windows or Linux)
* A terminal with Unicode support (any modern one). For legacy terminals set *Settings > Symbols > ASCII only*.

## Install USwap

### With pipx (recommended)

```bash
git clone https://github.com/YOUR-USER/uswap.git
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
./scripts/install.sh --uninstall      # Linux menu entries
pipx uninstall uswap                  # the program
```

Windows: `scripts\install.ps1 -Uninstall`, then `pipx uninstall uswap`. Your settings file is left in place; delete the `uswap` config folder to remove it.
