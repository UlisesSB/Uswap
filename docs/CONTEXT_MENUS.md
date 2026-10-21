# Context-menu integration

The main installers (`install.sh`, `install.ps1`, `USwap-Setup.exe`) already do all of this. This page explains what they set up and how to manage it by hand. Everything is **per-user**: no administrator rights, nothing outside your home/profile.

## Linux

```bash
./scripts/menu-linux.sh              # file managers found on this machine
./scripts/menu-linux.sh --all        # all supported ones
./scripts/menu-linux.sh --uninstall
```

File managers start programs without a terminal, so the script creates a launcher, `~/.local/bin/uswap-popup`, that opens a terminal emulator and runs `uswap` in it. It uses `$TERMINAL` if set, otherwise the first of: `x-terminal-emulator`, `gnome-terminal`, `konsole`, `xfce4-terminal`, `mate-terminal`, `kitty`, `alacritty`, `foot`, `wezterm`, `lxterminal`, `xterm`.

| File manager | Mechanism | Where it appears |
|--------------|-----------|------------------|
| Nautilus (GNOME) | script in `~/.local/share/nautilus/scripts/` | right-click > Scripts > Convert with USwap |
| Nemo (Cinnamon) | `~/.local/share/nemo/actions/uswap.nemo_action` | right-click |
| Dolphin (KDE) | `~/.local/share/kio/servicemenus/uswap.desktop` | right-click |
| Thunar (XFCE) | block in `~/.config/Thunar/uca.xml` (backup: `uca.xml.uswap.bak`) | right-click |

Restart the file manager afterwards (`nautilus -q`, `thunar -q`, ...). Selecting several files opens batch mode.

If you use another terminal, set it in your shell profile: `export TERMINAL=kitty`.

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts\menu-windows.ps1
powershell -ExecutionPolicy Bypass -File scripts\menu-windows.ps1 -Uninstall
```

Writes `HKCU\Software\Classes\*\shell\USwap` with the command `"<path>\uswap.exe" "%1"` and copies the icon to `%LOCALAPPDATA%\uswap`. `uswap.exe` is a console program, so Explorer opens a console window for it.

* On Windows 11 the entry is under **Show more options** (or Shift+F10).
* With several files selected, Explorer starts one `uswap` per file (and may hide the entry beyond its own selection limit). For many files use `uswap "*.png" --to webp` or the dashboard's batch mode.
* If `uswap` is not on PATH, pass `-UswapPath C:\full\path\to\uswap.exe`.

## Troubleshooting

* *Entry does not appear*: restart the file manager / Explorer, and check `uswap --version` works in a fresh terminal.
* *Window flashes and closes*: run `uswap FILE` from a terminal to see the error; failures normally keep the window open.
* *No terminal found (Linux)*: install one or set `TERMINAL`.
