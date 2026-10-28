#!/usr/bin/env python3
"""USwap - convert any file from your terminal or your right-click menu.

    uswap                     interactive menu
    uswap FILE                pick a format and convert (used by the right-click menu)
    uswap FILE... --to FMT    convert without asking (files, folders or globs)
    uswap --update            update USwap (only if you want to)

Only the Python standard library is used. FFmpeg does images, audio and video;
optional add-ons (Pandoc, Poppler, Typst, ImageMagick, LibreOffice) unlock more formats.

Copyright (c) 2026 Ulises Agustin Rodriguez - MIT License
https://github.com/UlisesSB/USwap
"""

from __future__ import annotations

import argparse
import fnmatch
import functools
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

__version__ = "2.1.0"
REPO = "UlisesSB/USwap"
WINDOWS = os.name == "nt"
FROZEN = getattr(sys, "frozen", False)  # the Windows installer build
if WINDOWS:
    DATA = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "USwap"
else:
    DATA = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "uswap"
ADDON_DIR = DATA / "addons"

# --------------------------------------------------------------------- formats
IMAGE, AUDIO, VIDEO, DOC = "image", "audio", "video", "document"

FORMATS = {  # ext -> (category, label)
    "png": (IMAGE, "PNG image"), "jpg": (IMAGE, "JPEG image"), "webp": (IMAGE, "WebP image"),
    "gif": (IMAGE, "GIF image"), "bmp": (IMAGE, "Bitmap image"), "tiff": (IMAGE, "TIFF image"),
    "ico": (IMAGE, "Windows icon"), "heic": (IMAGE, "HEIC photo (iPhone)"),
    "avif": (IMAGE, "AVIF image"), "svg": (IMAGE, "SVG vector image"),
    "mp3": (AUDIO, "MP3 audio"), "wav": (AUDIO, "WAV audio"), "flac": (AUDIO, "FLAC audio"),
    "ogg": (AUDIO, "Ogg Vorbis audio"), "opus": (AUDIO, "Opus audio"), "m4a": (AUDIO, "M4A audio"),
    "aac": (AUDIO, "AAC audio"), "wma": (AUDIO, "Windows Media audio"),
    "aiff": (AUDIO, "AIFF audio"), "amr": (AUDIO, "AMR voice audio"),
    "mp4": (VIDEO, "MP4 video"), "mkv": (VIDEO, "Matroska video"), "webm": (VIDEO, "WebM video"),
    "mov": (VIDEO, "QuickTime video"), "avi": (VIDEO, "AVI video"),
    "wmv": (VIDEO, "Windows Media video"), "flv": (VIDEO, "Flash video"),
    "3gp": (VIDEO, "3GP phone video"), "mpeg": (VIDEO, "MPEG video"), "ts": (VIDEO, "MPEG-TS video"),
    "pdf": (DOC, "PDF document"), "docx": (DOC, "Word document"), "odt": (DOC, "OpenDocument text"),
    "rtf": (DOC, "Rich Text"), "epub": (DOC, "EPUB e-book"), "html": (DOC, "Web page"),
    "md": (DOC, "Markdown"), "txt": (DOC, "Plain text"), "doc": (DOC, "Word 97 document"),
    "xlsx": (DOC, "Excel spreadsheet"), "xls": (DOC, "Excel 97 spreadsheet"),
    "ods": (DOC, "OpenDocument spreadsheet"), "pptx": (DOC, "PowerPoint deck"),
    "ppt": (DOC, "PowerPoint 97 deck"), "odp": (DOC, "OpenDocument presentation"),
}
ALIASES = {"jpeg": "jpg", "jpe": "jpg", "jfif": "jpg", "tif": "tiff", "htm": "html",
           "markdown": "md", "text": "txt", "oga": "ogg", "m4v": "mp4", "qt": "mov",
           "heif": "heic", "hif": "heic", "aif": "aiff", "mpg": "mpeg", "m2ts": "ts",
           "mts": "ts", "3g2": "3gp"}

IMG = ["png", "jpg", "webp", "gif", "bmp", "tiff", "ico"]
AUD = ["mp3", "wav", "flac", "ogg", "opus", "m4a", "aac"]
VID = ["mp4", "mkv", "webm", "mov", "avi"]
DOCS = ["docx", "odt", "md", "txt", "html", "rtf", "epub"]
OFFICE = ["docx", "odt", "rtf", "doc", "xlsx", "xls", "ods", "pptx", "ppt", "odp"]

ROUTES = [  # (engine, from, to) - order decides menu order and which engine wins
    ("ffmpeg", IMG, IMG + ["pdf"]),
    ("magick", ["heic", "avif", "svg"], IMG + ["pdf"]),
    ("ffmpeg", AUD + ["wma", "aiff", "amr"], AUD),
    ("ffmpeg", VID + ["wmv", "flv", "3gp", "mpeg", "ts"], VID + ["gif"] + AUD),
    ("pandoc", DOCS, DOCS),
    ("office", OFFICE, ["pdf"]),
    ("typst", DOCS, ["pdf"]),
    ("poppler", ["pdf"], ["txt", "png", "jpg"]),
]
ENGINE_TOOLS = {"ffmpeg": ["ffmpeg"], "magick": ["magick"], "pandoc": ["pandoc"],
                "typst": ["pandoc", "typst"], "office": ["soffice"],
                "poppler": ["pdftoppm", "pdftotext"]}

PANDOC_IN = {"md": "markdown", "txt": "markdown", "html": "html", "docx": "docx",
             "odt": "odt", "rtf": "rtf", "epub": "epub"}
PANDOC_OUT = {"md": "gfm", "txt": "plain", "html": "html5", "docx": "docx",
              "odt": "odt", "rtf": "rtf", "epub": "epub"}

X264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"]
AAC = ["-c:a", "aac", "-b:a", "160k"]
ONE = ["-frames:v", "1"]
FFMPEG_ARGS = {
    "png": ONE, "bmp": ONE, "tiff": ONE,
    "jpg": ["-filter_complex", "[0:v]format=rgba,split[a][b];[a]drawbox=c=white:t=fill[bg];"
            "[bg][b]overlay=format=auto,format=yuvj444p", *ONE, "-q:v", "2"],
    "webp": ["-c:v", "libwebp", "-quality", "90", "-loop", "0"],
    "ico": ["-vf", "scale='min(256,iw)':'min(256,ih)':force_original_aspect_ratio=decrease", *ONE],
    "mp3": ["-vn", "-c:a", "libmp3lame", "-q:a", "2"],
    "wav": ["-vn", "-c:a", "pcm_s16le"],
    "flac": ["-vn", "-c:a", "flac"],
    "ogg": ["-vn", "-c:a", "libvorbis", "-q:a", "5"],
    "opus": ["-vn", "-c:a", "libopus", "-b:a", "128k"],
    "m4a": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    "aac": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    "mp4": [*X264, *AAC, "-movflags", "+faststart"],
    "mkv": [*X264, *AAC],
    "mov": [*X264, *AAC],
    "webm": ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-c:a", "libopus", "-b:a", "128k"],
    "avi": ["-c:v", "mpeg4", "-q:v", "4", "-c:a", "libmp3lame", "-q:a", "4"],
}
GIF_FROM_VIDEO = ["-an", "-vf", "fps=12,scale=480:-1:flags=lanczos,split[a][b];"
                  "[a]palettegen[p];[b][p]paletteuse", "-loop", "0"]
GIF_FROM_IMAGE = ["-vf", "split[a][b];[a]palettegen=reserve_transparent=1[p];[b][p]paletteuse",
                  "-loop", "0"]

# ------------------------------------------------------------------- add-ons
# Optional tools, installed only when the user asks (menu > Optional formats).
#   ("github", repo, {arch: asset pattern})  portable download into ADDON_DIR
#   ("pkg", {package manager: [packages]})   Linux package manager (sudo)
#   ("winget", package id)                   Windows Package Manager
ADDONS = {
    "documents": {
        "name": "Documents", "engine": "pandoc", "tools": ["pandoc"],
        "what": "docx, odt, md, html, rtf, epub, txt to each other",
        "linux": ("github", "jgm/pandoc", {"x86_64": "pandoc-*-linux-amd64.tar.gz",
                                           "aarch64": "pandoc-*-linux-arm64.tar.gz"}),
        "windows": ("github", "jgm/pandoc", {"x86_64": "pandoc-*-windows-x86_64.zip"}),
    },
    "pdf": {
        "name": "PDF reader", "engine": "poppler", "tools": ["pdftoppm", "pdftotext"],
        "what": "pdf to txt, png, jpg (one image per page)",
        "linux": ("pkg", {"apt": ["poppler-utils"], "dnf": ["poppler-utils"],
                          "pacman": ["poppler"], "zypper": ["poppler-tools"]}),
        "windows": ("github", "oschwartz10612/poppler-windows", {"x86_64": "Release-*.zip"}),
    },
    "docpdf": {
        "name": "Documents to PDF", "engine": "typst", "tools": ["typst"], "needs": "documents",
        "what": "md, docx, html, epub... to pdf (Typst)",
        "linux": ("github", "typst/typst", {"x86_64": "typst-x86_64-unknown-linux-musl.tar.xz",
                                            "aarch64": "typst-aarch64-unknown-linux-musl.tar.xz"}),
        "windows": ("github", "typst/typst", {"x86_64": "typst-x86_64-pc-windows-msvc.zip"}),
    },
    "images": {
        "name": "Extra images", "engine": "magick", "tools": ["magick"],
        "what": "heic (iPhone), avif, svg to any image or pdf (ImageMagick)",
        "linux": ("pkg", {"apt": ["imagemagick", "librsvg2-bin"],
                          "dnf": ["ImageMagick", "librsvg2-tools"],
                          "pacman": ["imagemagick", "libheif", "librsvg"],
                          "zypper": ["ImageMagick", "rsvg-convert"]}),
        "windows": ("winget", "ImageMagick.ImageMagick"),
    },
    "office": {
        "name": "Office to PDF", "engine": "office", "tools": ["soffice"],
        "what": "docx, xlsx, pptx, odt... to an exact pdf (LibreOffice, big)",
        "linux": ("pkg", {"apt": ["libreoffice-writer", "libreoffice-calc", "libreoffice-impress"],
                          "dnf": ["libreoffice-writer", "libreoffice-calc", "libreoffice-impress"],
                          "pacman": ["libreoffice-fresh"],
                          "zypper": ["libreoffice-writer", "libreoffice-calc",
                                     "libreoffice-impress"]}),
        "windows": ("winget", "TheDocumentFoundation.LibreOffice"),
    },
}
ENGINE_ADDON = {a["engine"]: key for key, a in ADDONS.items()}
PACKAGE_MANAGERS = {  # name -> (binary that reveals it, install command)
    "apt": ("apt-get", ["apt-get", "install", "-y"]),
    "dnf": ("dnf", ["dnf", "install", "-y"]),
    "pacman": ("pacman", ["pacman", "-S", "--needed", "--noconfirm"]),
    "zypper": ("zypper", ["zypper", "--non-interactive", "install"]),
}


def norm(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    return ALIASES.get(ext, ext)


def setup_path() -> None:
    """Make bundled tools (Windows installer) and portable add-ons reachable."""
    extra = [str(Path(sys.executable).parent / "tools")] if FROZEN else []
    for f in sorted(ADDON_DIR.glob("*/path.txt")):
        extra.append(f.read_text(encoding="utf-8").strip())
    path = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join([p for p in extra if p not in path] + [path])
    find.cache_clear()


@functools.lru_cache(maxsize=None)
def find(tool: str) -> str | None:
    """Full path of an external tool, or None."""
    names = {"soffice": ["soffice", "libreoffice"],
             "magick": ["magick"] if WINDOWS else ["magick", "convert"]}.get(tool, [tool])
    for name in names:
        if path := shutil.which(name):
            return path
    if WINDOWS:  # winget installs these outside PATH until the next login
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pattern = {"soffice": rf"{pf}\LibreOffice\program\soffice.com",
                   "magick": rf"{pf}\ImageMagick-*\magick.exe"}.get(tool)
        hits = sorted(glob.glob(pattern)) if pattern else []
        return hits[-1] if hits else None
    return None


def engine_ok(engine: str) -> bool:
    return all(find(t) for t in ENGINE_TOOLS[engine])


def targets_for(ext: str, installed: bool = True) -> list[str]:
    """Formats `ext` can become (with the tools installed now, or with every add-on)."""
    out: list[str] = []
    for engine, sources, targets in ROUTES:
        if ext in sources and (not installed or engine_ok(engine)):
            out += [t for t in targets if t != ext and t not in out]
    return out


def route(ext: str, target: str) -> str | None:
    for engine, sources, targets in ROUTES:
        if ext in sources and target in targets and engine_ok(engine):
            return engine
    return None


def missing_addons(ext: str) -> list[str]:
    """Add-ons that would unlock more formats for `ext`."""
    keys = []
    for engine, sources, _ in ROUTES:
        key = ENGINE_ADDON.get(engine)
        if ext in sources and key and not engine_ok(engine) and key not in keys:
            keys.append(key)
    return keys


# ------------------------------------------------------------------- detection
def sniff(path: Path) -> str | None:
    """Real format from the first bytes; the extension is only a fallback."""
    try:
        with path.open("rb") as fh:
            h = fh.read(4096)
    except OSError:
        return None
    declared = norm(path.suffix)
    if h.startswith(b"\x89PNG"): return "png"
    if h.startswith(b"\xff\xd8\xff"): return "jpg"
    if h[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if h.startswith(b"BM") and len(h) > 14: return "bmp"
    if h[:4] in (b"II*\x00", b"MM\x00*"): return "tiff"
    if h.startswith(b"\x00\x00\x01\x00"): return "ico"
    if h.startswith(b"RIFF"): return {b"WEBP": "webp", b"WAVE": "wav", b"AVI ": "avi"}.get(h[8:12])
    if h.startswith(b"FORM") and h[8:12] in (b"AIFF", b"AIFC"): return "aiff"
    if h.startswith(b"#!AMR"): return "amr"
    if h.startswith(b"FLV"): return "flv"
    if h.startswith(b"fLaC"): return "flac"
    if h.startswith(b"OggS"): return "opus" if b"OpusHead" in h[:128] else "ogg"
    if h.startswith(b"\x1a\x45\xdf\xa3"): return "webm" if b"webm" in h[:64] else "mkv"
    if h.startswith(b"\x30\x26\xb2\x75\x8e\x66\xcf\x11"):  # ASF: wma or wmv
        return declared if declared in ("wma", "wmv") else "wmv"
    if h.startswith(b"\x00\x00\x01\xba"): return "mpeg"
    if len(h) > 376 and h[0] == h[188] == h[376] == 0x47: return "ts"
    if h[4:8] == b"ftyp":
        brand, compat = h[8:12], h[16:int.from_bytes(h[:4], "big")]
        if brand in (b"avif", b"avis") or b"avif" in compat: return "avif"
        if brand in (b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1") or b"heic" in compat:
            return "heic"
        if brand.startswith(b"3g"): return "3gp"
        return "mov" if brand == b"qt  " else "m4a" if brand.startswith(b"M4A") else "mp4"
    if h.startswith(b"%PDF"): return "pdf"
    if h.startswith(b"{\\rtf"): return "rtf"
    if h.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):  # old Office files
        return declared if declared in ("doc", "xls", "ppt") else None
    if h.startswith(b"ID3") or (len(h) > 1 and h[0] == 0xFF and h[1] & 0xE0 == 0xE0):
        return "aac" if h[1] & 0xF6 == 0xF0 else "mp3"
    if h.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())
                for inner, ext in (("word/document.xml", "docx"), ("xl/workbook.xml", "xlsx"),
                                   ("ppt/presentation.xml", "pptx")):
                    if inner in names:
                        return ext
                if "mimetype" in names:
                    mt = z.read("mimetype").strip().decode("ascii", "ignore")
                    return {"application/vnd.oasis.opendocument.text": "odt",
                            "application/vnd.oasis.opendocument.spreadsheet": "ods",
                            "application/vnd.oasis.opendocument.presentation": "odp",
                            "application/epub+zip": "epub"}.get(mt)
        except (zipfile.BadZipFile, OSError):
            pass
        return None
    if b"\x00" not in h:  # text formats
        if declared == "svg" or (b"<svg" in h[:2048] and declared in ("", "xml")):
            return "svg"
        if declared in ("md", "txt", "html"):
            return declared
    return None


def detect(path: Path) -> str | None:
    ext = sniff(path)
    if ext is None and FORMATS.get(norm(path.suffix), (None,))[0] in (AUDIO, VIDEO):
        ext = norm(path.suffix)  # odd headers (some mp3/avi): trust the name
    return ext


# ------------------------------------------------------------------ conversion
class Failed(Exception):
    pass


def last(exc: Exception) -> str:
    lines = str(exc).strip().splitlines()
    return lines[-1] if lines else "failed"


def free(path: Path) -> Path:
    """`photo.jpg`, or `photo (1).jpg` if that already exists."""
    candidate, n = path, 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        n += 1
    return candidate


def output_path(src: Path, target: str) -> Path:
    return free(src.with_name(f"{src.stem}.{target}"))


def run(cmd: list[str], on_line=None) -> None:
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                                errors="replace")
    except OSError as exc:
        raise Failed(f"cannot run {Path(cmd[0]).name}: {exc}") from None
    log: list[str] = []
    try:
        for line in proc.stdout:
            if not (on_line and on_line(line.strip())):
                log.append(line.rstrip())
        code = proc.wait()
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    if code:
        raise Failed("\n".join(log[-4:]) or f"{Path(cmd[0]).name} exited with code {code}")


def duration(src: Path) -> float:
    if not find("ffprobe"):
        return 0.0
    try:
        out = subprocess.run([find("ffprobe"), "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(src)], capture_output=True, text=True,
                             timeout=20)
        return float(out.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0


def ffmpeg(src: Path, ext: str, dst: Path, target: str, progress) -> None:
    cat = FORMATS[ext][0]
    if target == "gif":
        args = GIF_FROM_VIDEO if cat == VIDEO else GIF_FROM_IMAGE
    else:
        args = FFMPEG_ARGS[target]
    total = duration(src) if cat != IMAGE else 0.0

    def on_line(line: str) -> bool:
        key, _, value = line.partition("=")
        if key == "out_time_us" and total and value.isdigit():
            progress(min(int(value) / 1e6 / total, 0.99))
        return "=" in line and " " not in key  # True = progress line, not an error

    run([find("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-nostats",
         "-progress", "pipe:1", "-i", str(src), *args, str(dst)], on_line)


def magick(src: Path, dst: Path, target: str) -> None:
    extra = {"jpg": ["-background", "white", "-flatten", "-quality", "92"],
             "bmp": ["-background", "white", "-flatten"],
             "ico": ["-resize", "256x256>"]}.get(target, [])
    run([find("magick"), f"{src}[0]", *extra, str(dst)])


def jpeg_info(data: bytes) -> tuple[int, int, int]:
    """(width, height, color components) from a JPEG's frame header."""
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01, 0xFF) or 0xD0 <= marker <= 0xD7:
            i += 2 if marker != 0xFF else 1
            continue
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h = int.from_bytes(data[i + 5:i + 7], "big")
            w = int.from_bytes(data[i + 7:i + 9], "big")
            return w, h, data[i + 9]
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    raise Failed("could not read the image size")


def images_to_pdf(items: list[tuple[Path, str]], dst: Path, progress=lambda f: None) -> None:
    """One PDF page per image, fitted to A4. Pure Python: the JPEG goes in as is."""
    pages = []
    with tempfile.TemporaryDirectory() as tmp:
        for n, (src, ext) in enumerate(items):
            jpg = Path(tmp, f"{n}.jpg")
            try:
                if route(ext, "jpg") == "magick":
                    magick(src, jpg, "jpg")
                else:
                    run([find("ffmpeg"), "-y", "-loglevel", "error", "-i", str(src),
                         *FFMPEG_ARGS["jpg"], str(jpg)])
            except Failed as exc:
                raise Failed(f"{src.name}: {last(exc)}") from None
            pages.append(jpg.read_bytes())
            progress((n + 1) / len(items) * 0.9)
    objs: list[bytes] = [b"", b""]  # 1 catalog, 2 page tree
    kids = []
    for data in pages:
        w, h, comps = jpeg_info(data)
        box = (842, 595) if w > h else (595, 842)  # A4 in points
        scale = min(box[0] / w, box[1] / h, 0.75)  # never bigger than 96 dpi
        pw, ph = w * scale, h * scale
        space = {1: b"/DeviceGray", 4: b"/DeviceCMYK"}.get(comps, b"/DeviceRGB")
        objs.append(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace %s "
                    b"/BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n"
                    % (w, h, space, len(data)) + data + b"\nendstream")
        draw = b"q %.2f 0 0 %.2f 0 0 cm /Im Do Q" % (pw, ph)
        objs.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(draw), draw))
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Resources "
                    b"<< /XObject << /Im %d 0 R >> >> /Contents %d 0 R >>"
                    % (pw, ph, len(objs) - 1, len(objs)))
        kids.append(len(objs))
    objs[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    pdf, offsets = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"), []
    for n, obj in enumerate(objs, 1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n%s\nendobj\n" % (n, obj)
    xref = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    pdf += b"".join(b"%010d 00000 n \n" % off for off in offsets)
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    dst.write_bytes(bytes(pdf))


def office_pdf(src: Path, dst: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        profile = Path(tmp, "profile").as_uri()  # own profile: works even if LibreOffice is open
        run([find("soffice"), f"-env:UserInstallation={profile}", "--headless",
             "--convert-to", "pdf", "--outdir", tmp, str(src)])
        made = Path(tmp, src.stem + ".pdf")
        if not made.exists():
            raise Failed("LibreOffice did not create the PDF")
        shutil.move(str(made), str(dst))


def pdf_pages(src: Path, dst: Path, target: str) -> list[Path]:
    if target == "txt":
        run([find("pdftotext"), "-layout", "-enc", "UTF-8", str(src), str(dst)])
        return [dst]
    prefix = dst.with_suffix("")
    run([find("pdftoppm"), "-png" if target == "png" else "-jpeg", "-r", "150", str(src),
         str(prefix)])
    pages = sorted(prefix.parent.glob(glob.escape(prefix.name) + "-*." + target),
                   key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    if len(pages) == 1:
        pages[0].replace(dst)
        return [dst]
    return pages


def convert(src: Path, ext: str, target: str, progress=lambda f: None) -> list[Path]:
    """Convert `src` (real format `ext`) to `target`. Returns the files created."""
    engine = route(ext, target)
    if engine is None:
        raise Failed(f"cannot go from {ext} to {target}")
    dst = output_path(src, target)
    try:
        if engine == "poppler":
            return pdf_pages(src, dst, target)
        if target == "pdf" and engine in ("ffmpeg", "magick"):
            images_to_pdf([(src, ext)], dst, progress)
        elif engine == "ffmpeg":
            ffmpeg(src, ext, dst, target, progress)
        elif engine == "magick":
            magick(src, dst, target)
        elif engine == "office":
            office_pdf(src, dst)
        else:  # pandoc, or pandoc + typst for pdf
            cmd = [find("pandoc"), str(src), "-f", PANDOC_IN[ext], "-o", str(dst)]
            if engine == "typst":
                cmd += [f"--pdf-engine={find('typst')}"]
            else:
                cmd += ["-t", PANDOC_OUT[target]]
            if target in ("html", "pdf"):
                cmd += ["-s", "--metadata", f"title={src.stem}"]
            run(cmd)
        return [dst]
    except BaseException:
        dst.unlink(missing_ok=True)
        raise


def scan(paths: list[Path]) -> list[tuple[Path, str]]:
    """Supported files among `paths` (folders are opened, not recursively)."""
    found = []
    for p in paths:
        for f in sorted(p.iterdir()) if p.is_dir() else [p]:
            if f.is_file() and not f.name.startswith(".") and (ext := detect(f)):
                found.append((f, ext))
    return found


# --------------------------------------------------------- internet: add-ons, updates
def http(url: str, timeout: float = 15):
    req = urllib.request.Request(url, headers={"User-Agent": f"USwap/{__version__}"})
    return urllib.request.urlopen(req, timeout=timeout)


def latest_release(timeout: float = 10) -> dict:
    with http(f"https://api.github.com/repos/{REPO}/releases/latest", timeout) as r:
        return json.load(r)


def github_asset(repo: str, pattern: str) -> tuple[str, str]:
    with http(f"https://api.github.com/repos/{repo}/releases/latest") as r:
        for asset in json.load(r)["assets"]:
            if fnmatch.fnmatch(asset["name"], pattern):
                return asset["name"], asset["browser_download_url"]
    raise Failed(f"no {pattern} in the latest {repo} release")


def download(url: str, dest: Path, label: str) -> None:
    with http(url, 60) as r, open(dest, "wb") as fh:
        total, done = int(r.headers.get("Content-Length") or 0), 0
        while chunk := r.read(1 << 16):
            fh.write(chunk)
            done += len(chunk)
            bar(done / total if total else 0, f"{label}  {size(done)}")
    bar(1, label)
    out("")


def version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", v)[:3])


def newer(v: str) -> bool:
    return bool(v) and version_tuple(v) > version_tuple(__version__)


UPDATE: str | None = None  # newer version found by check_updates()


def check_updates() -> None:
    """At most once a day, in the background, ask GitHub for the latest version."""
    global UPDATE
    if os.environ.get("USWAP_NO_UPDATE_CHECK"):
        return
    cache = DATA / "update.json"
    try:
        saved = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    if newer(saved.get("latest", "")):
        UPDATE = saved["latest"]
    if time.time() - saved.get("checked", 0) < 86400:
        return

    def work() -> None:
        global UPDATE
        try:
            latest = latest_release(4)["tag_name"].lstrip("v")
            DATA.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"checked": time.time(), "latest": latest}))
        except Exception:
            return
        UPDATE = latest if newer(latest) else None

    threading.Thread(target=work, daemon=True).start()


def machine() -> str:
    m = platform.machine().lower()
    return "aarch64" if m in ("arm64", "aarch64") else "x86_64"


def package_manager() -> str | None:
    for name, (binary, _) in PACKAGE_MANAGERS.items():
        if shutil.which(binary):
            return name
    return None


def sudo(cmd: list[str]) -> list[str]:
    return cmd if WINDOWS or os.geteuid() == 0 else ["sudo", *cmd]


def addon_ready(key: str) -> bool:
    return all(find(t) for t in ADDONS[key]["tools"])


def install_plan(key: str) -> tuple[str, list[str] | None]:
    """(what will happen, in words; command to run or None for a download)."""
    a = ADDONS[key]
    how = a["windows" if WINDOWS else "linux"]
    if how[0] == "github":
        return f"downloads it from github.com/{how[1]} (no admin rights needed)", None
    if how[0] == "winget":
        if not shutil.which("winget"):
            return "needs winget (App Installer, from the Microsoft Store)", []
        return f"installs {how[1]} with winget", [
            "winget", "install", "-e", "--id", how[1],
            "--accept-source-agreements", "--accept-package-agreements"]
    pm = package_manager()
    if not pm:
        return "no supported package manager found: install it yourself", []
    pkgs = how[1][pm]
    return f"installs {' '.join(pkgs)} with {pm} (asks for your password)", sudo(
        PACKAGE_MANAGERS[pm][1] + pkgs)


def install_addon(key: str) -> bool:
    """Install an add-on (and the one it needs). Prints its own progress."""
    a = ADDONS[key]
    if a.get("needs") and not addon_ready(a["needs"]) and not install_addon(a["needs"]):
        return False
    how = a["windows" if WINDOWS else "linux"]
    out(AMBER(f"  ► {a['name']}"))
    if how[0] == "github":
        pattern = how[2].get(machine())
        if not pattern:
            out(RED(f"  ✘ no download for {machine()}"))
            return False
        target = ADDON_DIR / key
        try:
            name, url = github_asset(how[1], pattern)
            with tempfile.TemporaryDirectory() as tmp:
                archive = Path(tmp, name)
                download(url, archive, name)
                shutil.rmtree(target, ignore_errors=True)
                target.mkdir(parents=True)
                if name.endswith(".zip"):
                    with zipfile.ZipFile(archive) as z:
                        z.extractall(target)
                else:
                    with tarfile.open(archive) as t:
                        safe = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
                        t.extractall(target, **safe)
            dirs = []
            for tool in a["tools"]:
                hit = next(target.rglob(tool + (".exe" if WINDOWS else "")), None)
                if hit is None:
                    raise Failed(f"{tool} not found inside {name}")
                hit.chmod(hit.stat().st_mode | 0o755)
                dirs.append(str(hit.parent))
            (target / "path.txt").write_text(os.pathsep.join(dict.fromkeys(dirs)), "utf-8")
        except Exception as exc:
            shutil.rmtree(target, ignore_errors=True)
            out(RED(f"  ✘ {last(exc) if isinstance(exc, Failed) else exc}"))
            return False
        setup_path()
    else:
        words, cmd = install_plan(key)
        if not cmd:
            out(RED(f"  ✘ {words}"))
            return False
        if cmd[:2] == ["sudo", "apt-get"] or cmd[0] == "apt-get":
            subprocess.call(sudo(["apt-get", "update", "-qq"]))
        sys.stdout.write("\x1b[?25h")
        code = subprocess.call(cmd)
        sys.stdout.write("\x1b[?25l")
        find.cache_clear()
        if code and "pacman" in cmd:
            out(AMBER("  tip: if pacman could not download, update first:  sudo pacman -Syu"))
    ok = addon_ready(key)
    out(OK(f"  ✔ {a['name']} is ready") if ok else RED(f"  ✘ {a['name']} was not installed"))
    if ok and WINDOWS and how[0] == "winget":
        out(DIM("    (if USwap does not see it yet, close and open it again)"))
    return ok


def remove_addon(key: str) -> bool:
    if (ADDON_DIR / key).is_dir():
        shutil.rmtree(ADDON_DIR / key, ignore_errors=True)
        setup_path()
        return True
    return False


def update() -> int:
    """Update USwap in place, only after the user says yes."""
    try:
        release = latest_release()
    except Exception:
        out(RED("  ✘ could not reach GitHub. Check your connection."))
        return 1
    latest = release["tag_name"].lstrip("v")
    if not newer(latest):
        out(OK(f"  ✔ USwap {__version__} is the latest version"))
        return 0
    out(f"  {TEXT('USwap')} {DIM(__version__)} {RED('►')} {AMBER(latest)}")
    if release.get("html_url"):
        out(DIM(f"  what's new: {release['html_url']}"))
    sys.stdout.write("\x1b[?25h")
    if input("  Update now? [y/N] ").strip().lower() not in ("y", "yes", "s", "si", "sí"):
        return 0
    if FROZEN:  # Windows installer: run the new installer over this one
        setup = next((a for a in release.get("assets", [])
                      if fnmatch.fnmatch(a["name"], "USwap-Setup-*.exe")), None)
        if setup is None:
            out(RED("  ✘ this release has no installer yet; get it from the releases page"))
            return 1
        dest = Path(tempfile.gettempdir(), setup["name"])
        download(setup["browser_download_url"], dest, setup["name"])
        subprocess.Popen([str(dest), "/SP-"], creationflags=0x00000008)  # DETACHED_PROCESS
        out(OK("  ✔ the installer is open; USwap will close now"))
        return 0
    repo = DATA / "source"
    repo = Path(repo.read_text(encoding="utf-8").strip()) if repo.is_file() else None
    if repo and (repo / ".git").is_dir() and shutil.which("git"):
        out(DIM(f"  updating {repo}"))
        if subprocess.call(["git", "-C", str(repo), "pull", "--ff-only"]) == 0:
            return subprocess.call(["bash", str(repo / "install.sh")])
        out(RED("  ✘ git pull failed (local changes?)"))
        return 1
    me = Path(os.path.realpath(__file__))
    if os.access(me, os.W_OK) and os.access(me.parent, os.W_OK):
        url = f"https://raw.githubusercontent.com/{REPO}/{release['tag_name']}/uswap.py"
        new = me.with_suffix(".new")
        download(url, new, "uswap.py")
        if b"__version__" not in new.read_bytes():
            new.unlink()
            out(RED("  ✘ the download looks broken; nothing was changed"))
            return 1
        new.chmod(me.stat().st_mode)
        new.replace(me)
        out(OK(f"  ✔ updated to {latest}"))
        return 0
    out(AMBER("  USwap was installed by your package manager: update it there"),
        DIM("    e.g.  paru -Syu   or   yay -Syu"))
    return 1


# ------------------------------------------------------------------ terminal UI
COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def rgb(hex_: str):
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return lambda s: f"\x1b[38;2;{r};{g};{b}m{s}\x1b[0m" if COLOR else s


RED, AMBER, TEXT, DIM, OK = (rgb(c) for c in ("#E8323F", "#FFB547", "#F2E8D5", "#8C847A", "#8BD17C"))
BOLD = (lambda s: f"\x1b[1m{s}\x1b[22m") if COLOR else (lambda s: s)
CATEGORY_COLOR = {IMAGE: AMBER, AUDIO: OK, VIDEO: RED, DOC: TEXT}
PLURAL = {IMAGE: "images", AUDIO: "audio files", VIDEO: "videos", DOC: "documents"}


def logo() -> list[str]:
    lines = [
        RED("  █  █ ▄▀▀▀▀") + "    " + BOLD(RED("US") + TEXT("wap")) + DIM(f"  v{__version__}"),
        RED("  █  █ ▀▀▀▀▄") + "    " + DIM("convert any file, right here"),
        RED("  ▀▄▄▀ ▄▄▄▄▀"),
        RED("  ─────────►"),
        AMBER("  ◄─────────"),
    ]
    if UPDATE:
        lines[2] += "    " + AMBER(f"▲ v{UPDATE} available") + DIM("  ·  uswap --update")
    return lines


if WINDOWS:
    import msvcrt

    def getkey(timeout: float | None = None) -> str | None:
        end = time.time() + (timeout or 0)
        while timeout is not None and not msvcrt.kbhit():
            if time.time() > end:
                return None
            time.sleep(0.03)
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(msvcrt.getwch(), "")
        if ch == "\x03":
            raise KeyboardInterrupt
        return {"\r": "enter", "\x1b": "esc", "\x08": "back"}.get(ch, ch)
else:
    import select
    import termios
    import tty

    def getkey(timeout: float | None = None) -> str | None:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            if timeout is not None and not select.select([fd], [], [], timeout)[0]:
                return None
            ch = os.read(fd, 1)
            if ch == b"\x1b":
                if not select.select([fd], [], [], 0.05)[0]:
                    return "esc"
                seq = os.read(fd, 8)[1:2]
                return {b"A": "up", b"B": "down", b"C": "right", b"D": "left"}.get(seq, "")
            return {b"\n": "enter", b"\r": "enter", b"\x7f": "back"}.get(
                ch, ch.decode("utf-8", "ignore"))
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def out(*lines: str) -> None:
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


def screen(*lines: str) -> None:
    sys.stdout.write("\x1b[2J\x1b[H")
    out("", *logo(), "", *lines)


def choose(lines: list[str], items: list[tuple[str, str]], keys: str = "") -> int | None:
    """Arrow-key menu. Returns the chosen index, or None on Esc/q."""
    pos = 0
    visible = [len(re.sub(r"\x1b\[[0-9;]*m", "", label)) for label, _ in items]
    items = [(label + " " * (max(visible) - n), hint) for (label, hint), n in zip(items, visible)]
    while True:
        rows = max(shutil.get_terminal_size().lines - len(lines) - 12, 5)
        top = min(max(pos - rows // 2, 0), max(len(items) - rows, 0))
        body = []
        for i in range(top, min(top + rows, len(items))):
            label, hint = items[i]
            num = f"{i + 1}" if i < 9 else " "
            if i == pos:
                body.append(f"  {RED('►')} {AMBER(num)}  {BOLD(TEXT(label))}  {DIM(hint)}")
            else:
                body.append(f"    {DIM(num)}  {TEXT(label)}  {DIM(hint)}")
        if len(items) > rows:
            body.append(DIM(f"       {pos + 1}/{len(items)}"))
        hint = keys or "↑↓ move   1-9 pick   Enter select   Esc back"
        screen(*lines, *body, "", DIM("  " + hint))
        seen = UPDATE
        while (k := getkey(1.0)) is None and UPDATE == seen:
            pass  # waiting; redraw only if the update check finds something
        if k is None:
            continue
        if k in ("up", "k"):
            pos = (pos - 1) % len(items)
        elif k in ("down", "j"):
            pos = (pos + 1) % len(items)
        elif k in ("enter", "right"):
            return pos
        elif k in ("esc", "q", "left", "back"):
            return None
        elif k.isdigit() and 0 < int(k) <= min(9, len(items)):
            return int(k) - 1


def ask(*lines: str) -> bool:
    screen(*lines, "", AMBER("  [y] yes   [n] no"))
    return getkey() in ("y", "Y", "s", "S", "enter")


def bar(fraction: float, label: str) -> None:
    width = 28
    done = int(width * fraction)
    sys.stdout.write(f"\r  {RED('█' * done)}{DIM('░' * (width - done))} "
                     f"{AMBER(f'{fraction * 100:3.0f}%')}  {TEXT(label[:60])}\x1b[K")
    sys.stdout.flush()


def size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def pause(seconds: float | None = None) -> None:
    out("", DIM("  press any key" + (" (or wait, closing...)" if seconds else "")))
    getkey(seconds)


def addon_hint(ext: str) -> str:
    names = [ADDONS[k]["name"] for k in missing_addons(ext)]
    return f"add-on: {', '.join(names)}  (uswap › Optional formats)" if names else ""


def convert_one(path: Path) -> int:
    """The right-click pop-up: show the file, pick a format, convert."""
    ext = detect(path)
    if not ext:
        screen(RED(f"  ✘ {path.name}"), DIM("    This file type is not supported."))
        pause()
        return 1
    cat, label = FORMATS[ext]
    targets = targets_for(ext)
    info = [f"  {DIM('file')}  {BOLD(TEXT(path.name))}",
            f"  {DIM('type')}  {CATEGORY_COLOR[cat](label)}  {DIM('·  ' + size(path.stat().st_size))}"]
    if norm(path.suffix) not in (ext, ""):
        info.append(AMBER(f"        named .{norm(path.suffix)} but it is really .{ext}"))
    if not targets:
        screen(*info, "", RED("  ✘ To convert this file you need an optional"),
               RED("    " + addon_hint(ext)))
        pause()
        return 1
    more = addon_hint(ext)
    pick = choose([*info, "", AMBER("  convert to"), ""],
                  [(t.upper().ljust(5), FORMATS[t][1]) for t in targets],
                  keys="↑↓ move   1-9 pick   Enter select   Esc back"
                       + (f"\n  more formats with the {more}" if more else ""))
    if pick is None:
        return 130
    target = targets[pick]
    screen(*info, "")
    started = time.time()
    label = f"{path.name}  ►  {target.upper()}"
    try:
        bar(0, label)
        made = convert(path, ext, target, lambda f: bar(f, label))
    except Failed as exc:
        out("", "", RED("  ✘ conversion failed"),
            *(DIM("    " + line) for line in str(exc).splitlines()))
        pause()
        return 1
    bar(1, label)
    out("", "", OK(f"  ✔ done in {time.time() - started:.1f}s"))
    for f in made[:5]:
        out(DIM("    " + str(f)))
    if len(made) > 5:
        out(DIM(f"    ...and {len(made) - 5} more"))
    pause(2.5)
    return 0


def merge_name(files: list[tuple[Path, str]]) -> Path:
    folder = files[0][0].parent
    return free(folder / f"{folder.resolve().name or 'images'}.pdf")


def convert_many(files: list[tuple[Path, str]]) -> int:
    """Batch: one target format for a group of files of the same kind."""
    if not files:
        screen(RED("  ✘ No supported files here."))
        return 1
    groups: dict[str, list] = {}
    for f, ext in files:
        groups.setdefault(FORMATS[ext][0], []).append((f, ext))
    cats = list(groups)
    if len(cats) > 1:
        pick = choose([AMBER("  what do you want to convert?"), ""],
                      [(PLURAL[c], f"{len(groups[c])} files") for c in cats])
        if pick is None:
            return 130
        cats = [cats[pick]]
    files = groups[cats[0]]
    options: list[str] = []
    for _, ext in files:
        options += [t for t in targets_for(ext) if t not in options]
    if not options:
        screen(RED("  ✘ You need an optional " + addon_hint(files[0][1])))
        return 1
    pick = choose([f"  {BOLD(TEXT(str(len(files))))} {CATEGORY_COLOR[cats[0]](PLURAL[cats[0]])}",
                   "", AMBER("  convert all to"), ""],
                  [(t.upper(), FORMATS[t][1]) for t in options])
    if pick is None:
        return 130
    target = options[pick]
    todo = [(f, e) for f, e in files if e != target and target in targets_for(e)]
    if target == "pdf" and cats[0] == IMAGE and len(todo) > 1:
        pick = choose([AMBER(f"  {len(todo)} images to PDF"), ""],
                      [("one PDF per image", ""), ("all in a single PDF", "one page each")])
        if pick is None:
            return 130
        if pick == 1:
            dst = merge_name(todo)
            screen(AMBER(f"  joining {len(todo)} images into {dst.name}"), "")
            try:
                images_to_pdf(todo, dst, lambda x: bar(x, dst.name))
            except Failed as exc:
                out("", RED(f"  ✘ {last(exc)}"))
                return 1
            bar(1, dst.name)
            out("", "", OK(f"  ✔ {dst}"))
            return 0
    screen(AMBER(f"  converting {len(files)} files to {target.upper()}"), "")
    ok = failed = 0
    skipped = len(files) - len(todo)
    for f, ext in todo:
        label = f"{f.name}  ►  {target.upper()}"
        try:
            bar(0, label)
            convert(f, ext, target, lambda x: bar(x, label))
            sys.stdout.write("\r\x1b[K")
            out(f"  {OK('✔')}  {TEXT(f.name)}")
            ok += 1
        except Failed as exc:
            sys.stdout.write("\r\x1b[K")
            out(f"  {RED('✘')}  {TEXT(f.name)}  {DIM(last(exc)[:70])}")
            failed += 1
    out("", f"  {OK(f'{ok} converted')}   {DIM(f'{skipped} skipped')}   "
            f"{(RED if failed else DIM)(f'{failed} failed')}")
    return 1 if failed else 0


def browse(start: Path, want_folder: bool = False) -> Path | None:
    """Tiny file browser. Returns a file (or a folder when `want_folder`)."""
    here = start.resolve()
    while True:
        try:
            entries = sorted((p for p in here.iterdir() if not p.name.startswith(".")),
                             key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            entries = []
        dirs = [p for p in entries if p.is_dir()]
        files = [(p, detect(p)) for p in entries if p.is_file()]
        files = [(p, e) for p, e in files if e]
        items, paths = [], []
        if want_folder:
            n = len(files)
            items.append(("[ use this folder ]", f"{n} supported file{'s' * (n != 1)}"))
            paths.append(here)
        if here.parent != here:
            items.append(("..", "up"))
            paths.append(here.parent)
        for d in dirs:
            items.append((d.name + os.sep, ""))
            paths.append(d)
        if not want_folder:
            for p, e in files:
                items.append((p.name, FORMATS[e][1]))
                paths.append(p)
        if not items:
            items, paths = [("..", "up")], [here.parent]
        pick = choose([f"  {DIM('in')} {TEXT(str(here))}", ""], items)
        if pick is None:
            return None
        chosen = paths[pick]
        if chosen.is_dir() and not (want_folder and chosen == here):
            here = chosen
        else:
            return chosen


def addons_menu() -> None:
    while True:
        keys = list(ADDONS)
        items = [((OK("✔ ") if addon_ready(k) else "  ") + ADDONS[k]["name"], ADDONS[k]["what"])
                 for k in keys]
        pick = choose([AMBER("  optional formats"),
                       DIM("  extra tools, only downloaded if you want them"), ""], items)
        if pick is None:
            return
        key, a = keys[pick], ADDONS[keys[pick]]
        if addon_ready(key):
            if (ADDON_DIR / key).is_dir():
                if ask(f"  Remove {BOLD(TEXT(a['name']))}?", DIM(f"  {a['what']}")):
                    remove_addon(key)
            else:
                screen(OK(f"  ✔ {a['name']} is installed"),
                       DIM("    it was installed by your system; remove it from there"))
                pause()
            continue
        words, cmd = install_plan(key)
        lines = [f"  Install {BOLD(TEXT(a['name']))}?", DIM(f"  {a['what']}"), "",
                 TEXT(f"  USwap {words}.")]
        if a.get("needs") and not addon_ready(a["needs"]):
            lines.append(DIM(f"  It also installs {ADDONS[a['needs']]['name']}, which it needs."))
        if cmd == []:
            screen(*lines[:2], "", RED(f"  ✘ {words}"))
            pause()
        elif ask(*lines):
            screen()
            install_addon(key)
            pause()


def menu() -> int:
    while True:
        actions = [("convert", "Convert a file", "pick one file and a format"),
                   ("batch", "Convert a folder", "batch: every file of a kind at once"),
                   ("addons", "Optional formats", "documents, PDF, iPhone photos, Office..."),
                   ("doctor", "Check tools", "what is installed")]
        if UPDATE:
            actions.append(("update", f"Update to v{UPDATE}", "only if you want"))
        actions.append(("quit", "Quit", ""))
        pick = choose([], [(label, hint) for _, label, hint in actions],
                      keys="↑↓ move   Enter select   q quit")
        action = "quit" if pick is None else actions[pick][0]
        if action == "convert" and (f := browse(Path.cwd())):
            convert_one(f)
        elif action == "batch" and (d := browse(Path.cwd(), want_folder=True)):
            if convert_many(scan([d])) != 130:
                pause()
        elif action == "addons":
            addons_menu()
        elif action == "doctor":
            screen()
            doctor()
            pause()
        elif action == "update":
            screen()
            update()
            pause()
        elif action == "quit":
            return 0


# ------------------------------------------------------------------------- CLI
def doctor() -> int:
    for tool, use in (("ffmpeg", "images, audio and video"), ("ffprobe", "progress bars")):
        found = find(tool)
        out(f"  {OK('✔') if found else RED('✘')}  {TEXT(tool.ljust(18))} {DIM(use)}")
    if not find("ffmpeg"):
        pm = package_manager()
        cmd = ("winget install Gyan.FFmpeg" if WINDOWS else
               " ".join(sudo(PACKAGE_MANAGERS[pm][1] + ["ffmpeg"])) if pm else "")
        out("", DIM("  FFmpeg is required. Install it with:"), AMBER("    " + cmd))
    out("", DIM("  optional formats  (uswap › Optional formats, or uswap --install NAME)"))
    for key, a in ADDONS.items():
        mark = OK("✔") if addon_ready(key) else DIM("·")
        out(f"  {mark}  {TEXT(a['name'].ljust(18))} {DIM(key.ljust(10))} {DIM(a['what'])}")
    return 0 if find("ffmpeg") else 1


def list_formats() -> None:
    for cat in (IMAGE, AUDIO, VIDEO, DOC):
        exts = [e for e, (c, _) in FORMATS.items() if c == cat]
        out(f"  {CATEGORY_COLOR[cat](cat.ljust(9))} {TEXT(' '.join(exts))}")
    out("", DIM("  built in: images ↔ images and pdf, audio ↔ audio, video → video or audio"))
    for key, a in ADDONS.items():
        out(DIM(f"  add-on {key.ljust(10)} {a['what']}"))


def expand(items: list[str]) -> list[Path]:
    paths = []
    for item in items:
        p = Path(item).expanduser()
        if p.exists():
            paths.append(p)
        else:
            matched = [Path(m) for m in glob.glob(str(p))]
            if not matched:
                out(RED(f"  ✘ not found: {item}"))
            paths += matched
    return paths


def headless(paths: list[Path], target: str, merge: bool = False) -> int:
    target = norm(target)
    if target not in FORMATS:
        out(RED(f"  ✘ unknown format: {target}   (see uswap --formats)"))
        return 2
    named = {p for p in paths if p.is_file()}  # files inside folders are skipped quietly
    todo, failed = [], 0
    for f, ext in scan(paths):
        if ext == target or (f not in named and target not in targets_for(ext, installed=False)):
            continue
        if target not in targets_for(ext):
            hint = addon_hint(ext) if target in targets_for(ext, False) else ""
            out(f"{RED('✘')} {f.name}: cannot go from {ext} to {target}"
                + (f" without the {hint}" if hint else ""))
            failed += 1
        else:
            todo.append((f, ext))
    if merge and target == "pdf" and todo:
        images = [(f, e) for f, e in todo if FORMATS[e][0] == IMAGE]
        if images:
            dst = merge_name(images)
            try:
                images_to_pdf(images, dst)
                out(f"{OK('✔')} {len(images)} images → {dst}")
            except Failed as exc:
                out(f"{RED('✘')} {last(exc)}")
                failed += 1
            todo = [t for t in todo if t not in images]
    for f, ext in todo:
        try:
            for made in convert(f, ext, target):
                out(f"{OK('✔')} {f.name} → {made}")
        except Failed as exc:
            out(f"{RED('✘')} {f.name}: {last(exc)}")
            failed += 1
    return 1 if failed else 0


def open_terminal(args: list[str]) -> int:
    """Linux file managers start programs without a terminal: open one running USwap."""
    me = [sys.executable, os.path.realpath(__file__)]
    terms = [os.environ.get("TERMINAL", ""), "x-terminal-emulator", "konsole", "gnome-terminal",
             "kgx", "ptyxis", "xfce4-terminal", "mate-terminal", "tilix", "ghostty", "kitty",
             "alacritty", "foot", "wezterm", "lxterminal", "xterm"]
    term = next((t for t in terms if t and shutil.which(t)), None)
    if not term:
        subprocess.call(["notify-send", "USwap", "No terminal emulator found"])
        return 1
    name = Path(term).name
    if name in ("gnome-terminal", "kgx", "ptyxis", "tilix"):
        cmd = [term, "--", *me, *args]
    elif name in ("xfce4-terminal", "mate-terminal", "lxterminal"):
        cmd = [term, "-x", *me, *args]
    elif name in ("kitty", "foot"):
        cmd = [term, *me, *args]
    elif name == "wezterm":
        cmd = [term, "start", "--", *me, *args]
    else:
        cmd = [term, "-e", *me, *args]
    os.execvp(cmd[0], cmd)
    return 0


def setup_console() -> None:
    setup_path()
    if WINDOWS:
        os.system("")  # turns on ANSI colors in the classic Windows console
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    setup_console()
    ap = argparse.ArgumentParser(prog="uswap", description="Convert images, audio, video and "
                                 "documents. Run without arguments for the interactive menu.")
    ap.add_argument("files", nargs="*", help="files, folders or globs to convert")
    ap.add_argument("-t", "--to", metavar="FMT", help="convert straight to FMT, no questions")
    ap.add_argument("--merge", action="store_true", help="with --to pdf: all images in one PDF")
    ap.add_argument("--formats", action="store_true", help="list supported formats")
    ap.add_argument("--doctor", action="store_true", help="check installed tools and add-ons")
    ap.add_argument("--install", metavar="ADDON", choices=list(ADDONS),
                    help="install an optional add-on: " + ", ".join(ADDONS))
    ap.add_argument("--update", action="store_true", help="update USwap (asks first)")
    ap.add_argument("--terminal", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("-V", "--version", action="version", version=f"USwap {__version__}")
    args = ap.parse_args(argv)

    if args.terminal and not WINDOWS:
        return open_terminal(args.files)
    if args.formats:
        list_formats()
        return 0
    if args.doctor:
        return doctor()
    if args.install:
        return 0 if install_addon(args.install) else 1
    if args.update:
        return update()
    paths = expand(args.files)
    if args.files and not paths:
        return 2
    if args.to:
        return headless(paths, args.to, args.merge)
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        out("USwap needs an interactive terminal here. Use --to FMT for scripts.")
        return 2
    check_updates()
    sys.stdout.write("\x1b[?1049h\x1b[?25l")  # own screen (like vim), hide cursor
    try:
        if not paths:
            return menu()
        if len(paths) == 1 and paths[0].is_file():
            return convert_one(paths[0])
        code = convert_many(scan(paths))
        if code != 130:
            pause()
        return code
    except KeyboardInterrupt:
        return 130
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()


if __name__ == "__main__":
    sys.exit(main())
