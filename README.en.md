<p align="center">
  <img src="assets/banner.png" alt="USwap" width="560">
</p>

<p align="center">
  <b>Convert any file from your right-click menu or your terminal.</b><br>
  Images, audio, video and documents. No GUI, no internet, no fuss.
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-2.1.0-E8323F">
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
  █  █ ▄▀▀▀▀    USwap  v2.1.0
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
- **Only shows what makes sense.** A photo offers image formats and PDF; a video offers video formats and audio too, to extract the sound.
- **Converts whole folders.** Right-click a folder, or pick *Convert a folder* in the menu, and turn every image into WebP at once, or join them into a single PDF.
- **Light by default.** The base only needs FFmpeg. Less common formats are *add-ons* you install from the menu when you need them.
- **Works offline.** Everything happens on your computer. It only goes online to install an add-on or an update.
- **It's a single file.** `uswap.py` uses only the Python standard library.

## Install

### Windows

Download **`USwap-Setup-2.1.0.exe`** from [Releases](https://github.com/UlisesSB/USwap/releases/latest) and run it. FFmpeg comes bundled, so images, audio and video work right away. No administrator rights needed.

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

1. Installs Python 3 and FFmpeg with your distro's package manager (`apt`, `dnf`, `pacman` or `zypper`) if they are missing. It asks before using `sudo`.
2. Copies USwap to `~/.local/share/uswap` and puts the `uswap` command in `~/.local/bin`.
3. Adds **Convert with USwap** to the right-click menu of Nautilus (under *Scripts*), Nemo, Dolphin and Thunar.

It does not use `pip` or virtual environments. To uninstall: `bash install.sh --uninstall`.

> **Fedora:** the `ffmpeg-free` package has no H.264. To convert to MP4/MKV/MOV, install the full `ffmpeg` from [RPM Fusion](https://rpmfusion.org).

## Optional formats

Open `uswap` and choose **Optional formats**. Each add-on is installed only if you pick it, and can be removed later.

| Add-on | What it adds | Where it comes from |
|---|---|---|
| **Documents** | docx, odt, md, html, rtf, epub and txt to each other | [Pandoc](https://pandoc.org), direct download |
| **PDF reader** | pdf → txt, png, jpg (one image per page) | [Poppler](https://poppler.freedesktop.org) |
| **Documents to PDF** | md, docx, html, epub… → pdf | [Typst](https://typst.app), direct download (uses Documents) |
| **Extra images** | heic (iPhone photos), avif, svg → any image or pdf | [ImageMagick](https://imagemagick.org) |
| **Office to PDF** | docx, xlsx, pptx, odt… → a pdf identical to the original | [LibreOffice](https://libreoffice.org) (large) |

"Direct download" add-ons come from each project's official releases into USwap's folder, with no admin rights. The others use your Linux package manager, or `winget` on Windows. You can also install them from the terminal: `uswap --install documents`.

If you open a file that needs an add-on you don't have, USwap tells you which one.

## Usage

| How | What happens |
|---|---|
| Right-click › **Convert with USwap** | Pick the format with a number and it converts. |
| `uswap` | Menu: convert a file or a folder, optional formats, check tools. |
| `uswap photo.png` | Same as the right-click menu, from the terminal. |
| `uswap photo.png --to webp` | Converts straight away, no questions. |
| `uswap *.jpg --to pdf --merge` | Joins several images into a single PDF. |
| `uswap Downloads/ --to jpg` | Every supported file in a folder. |
| `uswap --install NAME` | Installs an add-on (`documents`, `pdf`, `docpdf`, `images`, `office`). |
| `uswap --doctor` | Shows which tools and add-ons are installed. |
| `uswap --formats` | Lists the supported formats. |
| `uswap --update` | Updates USwap, only if you confirm. |

**Keys:** `↑ ↓` or `j k` to move, `1`–`9` to pick directly, `Enter` to confirm, `Esc` or `q` to go back.

## Formats

| Type | In | Out | Needs |
|---|---|---|---|
| Image | png, jpg, webp, gif, bmp, tiff, ico | the same and pdf | — |
| Image | heic, avif, svg | png, jpg, webp, gif, bmp, tiff, ico, pdf | Extra images |
| Audio | mp3, wav, flac, ogg, opus, m4a, aac, wma, aiff, amr | mp3, wav, flac, ogg, opus, m4a, aac | — |
| Video | mp4, mkv, webm, mov, avi, wmv, flv, 3gp, mpeg, ts | mp4, mkv, webm, mov, avi, gif and any audio | — |
| Document | docx, odt, rtf, epub, html, md, txt | the same | Documents |
| Document | docx, odt, rtf, epub, html, md, txt | pdf | Documents to PDF |
| Office | docx, doc, xlsx, xls, pptx, ppt, odt, ods, odp, rtf | pdf | Office to PDF |
| PDF | pdf | txt, png, jpg | PDF reader |

## Updates

Once a day USwap checks whether there is a new version and, if so, shows a small notice (`▲ v2.2.0 available`) in the menu. It never downloads or changes anything on its own.

To update, run `uswap --update`, or choose *Update* in the menu, and confirm:

- **Windows:** downloads the new installer and opens it.
- **Linux (installed with `git clone`):** runs `git pull` and then `install.sh` again.

To turn the check off, set the environment variable `USWAP_NO_UPDATE_CHECK=1`.

## Support the project

USwap is free and open source. If it saves you time, you can help me keep improving it:

**Bank alias (Argentina): `uarodriguez.wb`** · Holder: Ulises Agustin Rodriguez

A GitHub star or a bug report helps a lot too.

## License

[MIT](LICENSE) © 2026 [Ulises Agustin Rodriguez](https://uarodriguez.com) · uarodriguez@computer.org

You can use, modify and redistribute it freely as long as you keep the copyright notice. FFmpeg (bundled with the Windows installer) and the add-ons have their own licenses: see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
