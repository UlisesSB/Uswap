# Development guide

```bash
git clone https://github.com/UlisesSB/uswap.git
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

* If you commit from Windows, keep the shell scripts executable for Linux users: `git update-index --chmod=+x install.sh scripts/menu-linux.sh`.
* Keyboard input: `termios`/`tty`/`select` on POSIX, `msvcrt` on Windows (`tui/keys.py`). Both branches normalize to the same key names.
* The Windows branch and `install.ps1` are exercised by CI only as far as imports and unit tests go; please test context-menu changes on a real Windows machine.

## Building the Windows installer

The `Release` workflow (`.github/workflows/release.yml`) runs on every `v*` tag: it tests, builds `uswap.exe` with PyInstaller (`--onedir`, so right-click launches stay fast), downloads FFmpeg/Pandoc/Poppler with `packaging/windows/fetch-tools.ps1`, compiles `packaging/windows/uswap.iss` with Inno Setup and attaches `USwap-Setup.exe` to the GitHub release. You can also run it manually from the *Actions* tab (*Release > Run workflow*): type a tag such as `v0.1.0` to publish the release, or leave it empty to just get the installer as a downloadable artifact of the run.

**Troubleshooting a missing release:**

1. *Actions* tab: is there a *Release* run? If not, the tag was probably pushed before the workflow files reached GitHub, or Actions is disabled (*Settings > Actions > General*). Push the commit first, then run the workflow manually with the tag.
2. If the run is red, open it and expand the failed step. The usual suspects are `Fetch FFmpeg, Pandoc and Poppler` (release asset names changed upstream) and `Build installer`.
3. If it is green but the release has no file, check *Settings > Actions > General > Workflow permissions* is *Read and write*.
4. Skip CI entirely: run `packaging\windows\build.ps1` on a Windows machine and attach `dist\USwap-Setup.exe` to the release by hand.

Locally on Windows (needs Python, PyInstaller and Inno Setup 6; `build.ps1` installs PyInstaller itself):

```powershell
python -m PyInstaller packaging/uswap_entry.py --name uswap --onedir --noconfirm --icon assets/uswap.ico --add-data "uswap/locales;uswap/locales" --collect-submodules PIL --collect-submodules watchdog --collect-submodules rich
./packaging/windows/fetch-tools.ps1
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" /DAppVersion=0.1.0 packaging\windows\uswap.iss
```

In the packaged build, `utils/system.py` prepends `<install dir>\tools` to `PATH` so the engines find the bundled binaries. Third-party licenses: `packaging/windows/THIRD_PARTY_NOTICES.txt`.

## Release checklist

1. Update `version` in `pyproject.toml` and `uswap/__init__.py`; update `CHANGELOG.md`.
2. `ruff check . && pytest`.
3. `python -m build` and inspect `dist/` (locales must be inside the wheel).
4. Tag `vX.Y.Z` and push the tag: the workflow publishes `USwap-Setup.exe`.
