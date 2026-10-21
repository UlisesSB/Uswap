# Development guide

```bash
git clone https://github.com/YOUR-USER/uswap.git
cd uswap
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Everyday commands

```bash
pytest                  # tests (engine tests are skipped when ffmpeg/pandoc/poppler are missing)
ruff check .            # lint
ruff format .           # format
python scripts/make_assets.py   # regenerate logo / banner / icon
python -m uswap         # run without installing
```

Install FFmpeg, Pandoc and Poppler locally to run the whole suite.

## Testing the TUI

Screens are driven by `render()` and `on_key()`, so logic such as `ListView` is unit-tested directly (`tests/test_widgets.py`). For end-to-end checks, run `uswap` inside a pseudo-terminal (Python's `pty`) and feed it keystrokes; [pyte](https://github.com/selectel/pyte) can render the captured output into a screen snapshot.

Isolate your real settings with `USWAP_CONFIG_DIR=/tmp/uswap-dev uswap`.

## Platform notes

* Keyboard input: `termios`/`tty`/`select` on POSIX, `msvcrt` on Windows (`tui/keys.py`). Both branches normalize to the same key names.
* The Windows branch and `install.ps1` are exercised by CI only as far as imports and unit tests go; please test context-menu changes on a real Windows machine.

## Release checklist

1. Update `version` in `pyproject.toml` and `uswap/__init__.py`; update `CHANGELOG.md`.
2. `ruff check . && pytest`.
3. `python -m build` and inspect `dist/` (locales must be inside the wheel).
4. Tag `vX.Y.Z` and publish.
