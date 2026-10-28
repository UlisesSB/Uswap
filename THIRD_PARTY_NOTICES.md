# Third-party notices

USwap's own code (`uswap.py`, the installers and the artwork) is released under the
[MIT License](LICENSE).

USwap does not include or link any third-party code. It runs the programs below as
separate processes, each under its own license.

## Bundled with the Windows installer

| Program | Used for | License | Source code |
|---|---|---|---|
| [FFmpeg](https://ffmpeg.org) (gyan.dev "essentials" build) | images, audio, video | GPL-3.0-or-later (this build includes GPL libraries such as x264) | https://ffmpeg.org/download.html · https://www.gyan.dev/ffmpeg/builds/ |
| [Python](https://www.python.org) runtime, embedded in `uswap.exe` by [PyInstaller](https://pyinstaller.org) | running USwap | PSF License 2.0 | https://github.com/python/cpython |

`ffmpeg.exe` and `ffprobe.exe` ship unmodified in the `tools` folder next to `uswap.exe`.

## Optional add-ons

These are **not** shipped with USwap. When a user picks one under *Optional formats*,
USwap downloads the official build from the project's own releases page or installs
it with the system package manager (`apt`, `dnf`, `pacman`, `zypper`, `winget`):

| Add-on | Program | License | Source code |
|---|---|---|---|
| Documents | [Pandoc](https://pandoc.org) | GPL-2.0-or-later | https://github.com/jgm/pandoc |
| PDF reader | [Poppler](https://poppler.freedesktop.org) | GPL-2.0-or-later | https://gitlab.freedesktop.org/poppler/poppler · Windows build: https://github.com/oschwartz10612/poppler-windows |
| Documents to PDF | [Typst](https://typst.app) | Apache-2.0 | https://github.com/typst/typst |
| Extra images | [ImageMagick](https://imagemagick.org) | ImageMagick License | https://github.com/ImageMagick/ImageMagick |
| Office to PDF | [LibreOffice](https://www.libreoffice.org) | MPL-2.0 | https://www.libreoffice.org/about-us/source-code/ |

The full license text of each program comes with its own download. If you need the
exact FFmpeg source for a version shipped in a USwap release, open an issue and it will
be provided.

Trademarks belong to their respective owners.
