# Third-party notices

USwap's own code (`uswap.py`, the installers and the artwork) is released under the
[MIT License](LICENSE).

USwap does not include or link any third-party code. It runs the programs below as
separate processes. On Linux you install them with your package manager. The Windows
installer (`USwap-Setup.exe`) ships unmodified copies of them in the `tools` folder,
next to `uswap.exe`. Each one keeps its own license:

| Program | Used for | License | Source code |
|---|---|---|---|
| [FFmpeg](https://ffmpeg.org) (gyan.dev "essentials" build) | images, audio, video | GPL-3.0-or-later (this build includes GPL libraries such as x264) | https://ffmpeg.org/download.html · https://www.gyan.dev/ffmpeg/builds/ |
| [Pandoc](https://pandoc.org) | documents | GPL-2.0-or-later | https://github.com/jgm/pandoc |
| [Poppler](https://poppler.freedesktop.org) (`pdftoppm`, `pdftotext`) and its libraries | PDF | GPL-2.0-or-later; bundled libraries under their own free licenses | https://gitlab.freedesktop.org/poppler/poppler · https://github.com/oschwartz10612/poppler-windows |
| [Python](https://www.python.org) runtime, embedded in `uswap.exe` by [PyInstaller](https://pyinstaller.org) | running USwap | PSF License 2.0 | https://github.com/python/cpython |

The full license text of each program comes with its original download and is
available at the source links above. If you need the exact source code of a version
shipped in a USwap release, open an issue and it will be provided.

Trademarks belong to their respective owners.
