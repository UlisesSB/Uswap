<p align="center">
  <img src="assets/banner.png" alt="USwap" width="560">
</p>

<p align="center">
  <b>Convert any file from your right-click menu or your terminal.</b><br>
  Images, audio, video and documents. No GUI, no internet, no fuss.
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-2.0.0-E8323F">
  <img alt="Platforms" src="https://img.shields.io/badge/Windows%20%7C%20Linux-17161B">
  <img alt="Python" src="https://img.shields.io/badge/python-3.8%2B-17161B">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-FFB547">
</p>

<p align="center">
  <a href="README.md">Español</a> · <b>English</b>
</p>

---

Right-click a file, choose **Convert with USwap**, a small terminal opens, press a number and you're done: the converted copy appears next to the original.

```text
  █  █ ▄▀▀▀▀    USwap  v2.0.0
  █  █ ▀▀▀▀▄    convert any file, right here
  ▀▄▄▀ ▄▄▄▄▀
  ─────────►
  ◄─────────

  file  holidays.mov
  type  QuickTime video  ·  48.2 MB

  convert to

  ► 1  MP4    MP4 video
    2  MKV    Matroska video
    3  WEBM   WebM video
    4  AVI    AVI video
    5  GIF    GIF image
    6  MP3    MP3 audio
    ...

  ↑↓ move   1-9 pick   Enter select   Esc back
```

## What it does

- **Detects the real file type.** It reads the first bytes instead of trusting the extension: a PNG renamed to `.jpg` is still treated as a PNG.
- **Never overwrites anything.** The original stays untouched. If `photo.jpg` already exists, it saves `photo (1).jpg`.
- **Only shows what makes sense.** A photo offers image formats; a video offers video formats and audio too, to extract the sound.
- **Converts whole folders.** Right-click a folder, or pick *Convert a folder* in the menu, and turn every image into WebP at once.
- **Works offline.** Everything happens on your computer.
- **It's a single file.** `uswap.py` uses only the Python standard library; the heavy lifting is done by [FFmpeg](https://ffmpeg.org), [Pandoc](https://pandoc.org) and [Poppler](https://poppler.freedesktop.org).

## Install

### Windows

Download **`USwap-Setup-2.0.0.exe`** from [Releases](https://github.com/UlisesSB/USwap/releases/latest) and run it. FFmpeg, Pandoc and Poppler come bundled, so there is nothing else to install. No administrator rights needed.

The installer adds:

- **Convert with USwap** to the right-click menu of files and folders. On Windows 11 it lives under *Show more options*.
- USwap to **Send to**, for converting several selected files together.
- The `uswap` command to your terminal.

### Linux

```bash
git clone https://github.com/UlisesSB/USwap.git
cd USwap
bash install.sh
```

The installer:

1. Installs Python 3, FFmpeg, Pandoc and Poppler with your distro's package manager (`apt`, `dnf`, `pacman` or `zypper`). It asks before using `sudo`.
2. Copies USwap to `~/.local/share/uswap` and puts the `uswap` command in `~/.local/bin`.
3. Adds **Convert with USwap** to the right-click menu of Nautilus (under *Scripts*), Nemo, Dolphin and Thunar.

It does not use `pip` or virtual environments, so it never hangs downloading dependencies.

To update: `git pull && bash install.sh`. To uninstall: `bash install.sh --uninstall`.

> **Fedora:** the `ffmpeg-free` package has no H.264. To convert to MP4/MKV/MOV, install the full `ffmpeg` from [RPM Fusion](https://rpmfusion.org).

## Usage

| How | What happens |
|---|---|
| Right-click › **Convert with USwap** | Pick the format with a number and it converts. |
| `uswap` | Menu: convert a file, convert a folder, check tools. |
| `uswap photo.png` | Same as the right-click menu, from the terminal. |
| `uswap photo.png --to webp` | Converts straight away, no questions. |
| `uswap *.wav --to mp3` | Several files at once. |
| `uswap Downloads/ --to jpg` | Every supported file in a folder. |
| `uswap --doctor` | Shows which tools are installed. |
| `uswap --formats` | Lists the supported formats. |

**Keys:** `↑ ↓` or `j k` to move, `1`–`9` to pick directly, `Enter` to confirm, `Esc` or `q` to go back.

## Formats

| Type | In | Out | Engine |
|---|---|---|---|
| Image | png, jpg, webp, gif, bmp, tiff, ico | the same | FFmpeg |
| Audio | mp3, wav, flac, ogg, opus, m4a, aac | the same | FFmpeg |
| Video | mp4, mkv, webm, mov, avi | mp4, mkv, webm, mov, avi, gif and any audio format | FFmpeg |
| Document | docx, odt, rtf, epub, html, md, txt | the same | Pandoc |
| PDF | pdf | txt, png, jpg (one image per page) | Poppler |

## Support the project

USwap is free and open source. If it saves you time, you can help me keep improving it:

**Bank alias (Argentina): `uarodriguez.wb`** · Holder: Ulises Agustin Rodriguez

A GitHub star or a bug report helps a lot too.

## License

[MIT](LICENSE) © 2026 [Ulises Agustin Rodriguez](https://uarodriguez.com) · uarodriguez@computer.org

You can use, modify and redistribute it freely as long as you keep the copyright notice. The tools bundled with the Windows installer have their own licenses: see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
