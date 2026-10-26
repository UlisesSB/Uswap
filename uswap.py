#!/usr/bin/env python3
"""USwap - convert any file from your terminal or your right-click menu.

    uswap                     interactive menu
    uswap FILE                pick a format and convert (used by the right-click menu)
    uswap FILE... --to FMT    convert without asking (files, folders or globs)

Only the Python standard library is used. The heavy lifting is done by
FFmpeg (images, audio, video), Pandoc (documents) and Poppler (PDF).

Copyright (c) 2026 Ulises Agustin Rodriguez - MIT License
https://github.com/UlisesSB/USwap
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

__version__ = "2.0.0"
WINDOWS = os.name == "nt"

# --------------------------------------------------------------------- formats
IMAGE, AUDIO, VIDEO, DOC = "image", "audio", "video", "document"

FORMATS = {  # ext -> (category, label)
    "png": (IMAGE, "PNG image"), "jpg": (IMAGE, "JPEG image"), "webp": (IMAGE, "WebP image"),
    "gif": (IMAGE, "GIF image"), "bmp": (IMAGE, "Bitmap image"), "tiff": (IMAGE, "TIFF image"),
    "ico": (IMAGE, "Windows icon"),
    "mp3": (AUDIO, "MP3 audio"), "wav": (AUDIO, "WAV audio"), "flac": (AUDIO, "FLAC audio"),
    "ogg": (AUDIO, "Ogg Vorbis audio"), "opus": (AUDIO, "Opus audio"), "m4a": (AUDIO, "M4A audio"),
    "aac": (AUDIO, "AAC audio"),
    "mp4": (VIDEO, "MP4 video"), "mkv": (VIDEO, "Matroska video"), "webm": (VIDEO, "WebM video"),
    "mov": (VIDEO, "QuickTime video"), "avi": (VIDEO, "AVI video"),
    "pdf": (DOC, "PDF document"), "docx": (DOC, "Word document"), "odt": (DOC, "OpenDocument text"),
    "rtf": (DOC, "Rich Text"), "epub": (DOC, "EPUB e-book"), "html": (DOC, "Web page"),
    "md": (DOC, "Markdown"), "txt": (DOC, "Plain text"),
}
ALIASES = {"jpeg": "jpg", "jpe": "jpg", "jfif": "jpg", "tif": "tiff", "htm": "html",
           "markdown": "md", "text": "txt", "oga": "ogg", "m4v": "mp4", "qt": "mov"}

AUDIO_OUT = ["mp3", "wav", "flac", "ogg", "opus", "m4a", "aac"]
TARGETS = {
    IMAGE: ["png", "jpg", "webp", "gif", "bmp", "tiff", "ico"],
    AUDIO: AUDIO_OUT,
    VIDEO: ["mp4", "mkv", "webm", "mov", "avi", "gif", *AUDIO_OUT],
    DOC: ["docx", "odt", "md", "txt", "html", "rtf", "epub"],  # PDF output needs LaTeX: skipped
}
PDF_TARGETS = ["txt", "png", "jpg"]
PANDOC_IN = {"md": "markdown", "txt": "markdown", "html": "html", "docx": "docx",
             "odt": "odt", "rtf": "rtf", "epub": "epub"}
PANDOC_OUT = {"md": "gfm", "txt": "plain", "html": "html5", "docx": "docx",
              "odt": "odt", "rtf": "rtf", "epub": "epub"}

X264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"]
AAC = ["-c:a", "aac", "-b:a", "160k"]
ONE = ["-frames:v", "1"]
FFMPEG_ARGS = {
    # images
    "png": ONE, "bmp": ONE, "tiff": ONE,
    "jpg": ["-filter_complex", "[0:v]format=rgba,split[a][b];[a]drawbox=c=white:t=fill[bg];"
            "[bg][b]overlay=format=auto,format=yuvj444p", *ONE, "-q:v", "2"],
    "webp": ["-c:v", "libwebp", "-quality", "90", "-loop", "0"],
    "ico": ["-vf", "scale='min(256,iw)':'min(256,ih)':force_original_aspect_ratio=decrease", *ONE],
    # audio
    "mp3": ["-vn", "-c:a", "libmp3lame", "-q:a", "2"],
    "wav": ["-vn", "-c:a", "pcm_s16le"],
    "flac": ["-vn", "-c:a", "flac"],
    "ogg": ["-vn", "-c:a", "libvorbis", "-q:a", "5"],
    "opus": ["-vn", "-c:a", "libopus", "-b:a", "128k"],
    "m4a": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    "aac": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    # video
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

TOOLS = {  # binary -> what it unlocks
    "ffmpeg": "images, audio and video",
    "ffprobe": "progress bar for audio/video",
    "pandoc": "documents (docx, odt, md, html...)",
    "pdftoppm": "PDF to image",
    "pdftotext": "PDF to text",
}


def norm(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    return ALIASES.get(ext, ext)


def has(tool: str) -> bool:
    return shutil.which(tool) is not None


def targets_for(ext: str) -> list[str]:
    """Formats `ext` can be converted to with the tools installed right now."""
    if ext == "pdf":
        need = {"txt": "pdftotext", "png": "pdftoppm", "jpg": "pdftoppm"}
        return [t for t in PDF_TARGETS if has(need[t])]
    cat = FORMATS[ext][0]
    if not has("pandoc" if cat == DOC else "ffmpeg"):
        return []
    return [t for t in TARGETS[cat] if t != ext]


# ------------------------------------------------------------------- detection
def sniff(path: Path) -> str | None:
    """Real format from the first bytes; the extension is only a fallback."""
    try:
        with path.open("rb") as fh:
            h = fh.read(4096)
    except OSError:
        return None
    if h.startswith(b"\x89PNG"): return "png"
    if h.startswith(b"\xff\xd8\xff"): return "jpg"
    if h[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if h.startswith(b"BM") and len(h) > 14: return "bmp"
    if h[:4] in (b"II*\x00", b"MM\x00*"): return "tiff"
    if h.startswith(b"\x00\x00\x01\x00"): return "ico"
    if h.startswith(b"RIFF"): return {b"WEBP": "webp", b"WAVE": "wav", b"AVI ": "avi"}.get(h[8:12])
    if h.startswith(b"fLaC"): return "flac"
    if h.startswith(b"OggS"): return "opus" if b"OpusHead" in h[:128] else "ogg"
    if h.startswith(b"\x1a\x45\xdf\xa3"): return "webm" if b"webm" in h[:64] else "mkv"
    if h[4:8] == b"ftyp":
        brand = h[8:12]
        return "mov" if brand == b"qt  " else "m4a" if brand.startswith(b"M4A") else "mp4"
    if h.startswith(b"%PDF"): return "pdf"
    if h.startswith(b"{\\rtf"): return "rtf"
    if h.startswith(b"ID3") or (len(h) > 1 and h[0] == 0xFF and h[1] & 0xE0 == 0xE0):
        return "aac" if h[1] & 0xF6 == 0xF0 else "mp3"
    if h.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
                if "word/document.xml" in names: return "docx"
                if "mimetype" in names:
                    mt = z.read("mimetype").strip()
                    return {b"application/vnd.oasis.opendocument.text": "odt",
                            b"application/epub+zip": "epub"}.get(mt)
        except (zipfile.BadZipFile, OSError):
            pass
        return None
    declared = norm(path.suffix)
    if declared in ("md", "txt", "html") and b"\x00" not in h:
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


def output_path(src: Path, target: str) -> Path:
    """`photo.png` -> `photo.jpg`, or `photo (1).jpg` if it already exists."""
    dst, n = src.with_suffix("." + target), 1
    while dst.exists():
        dst = src.with_name(f"{src.stem} ({n}).{target}")
        n += 1
    return dst


def run(cmd: list[str], on_line=None) -> None:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                            errors="replace")
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
    if not has("ffprobe"):
        return 0.0
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(src)], capture_output=True, text=True,
                             timeout=20)
        return float(out.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0


def convert(src: Path, ext: str, target: str, progress=lambda f: None) -> list[Path]:
    """Convert `src` (real format `ext`) to `target`. Returns the files created."""
    dst = output_path(src, target)
    try:
        if ext == "pdf":
            return convert_pdf(src, dst, target)
        cat = FORMATS[ext][0]
        if cat == DOC:
            cmd = ["pandoc", str(src), "-f", PANDOC_IN[ext], "-t", PANDOC_OUT[target],
                   "-o", str(dst)]
            if target == "html":
                cmd += ["-s", "--metadata", f"title={src.stem}"]
            run(cmd)
            return [dst]
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

        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostats",
             "-progress", "pipe:1", "-i", str(src), *args, str(dst)], on_line)
        return [dst]
    except BaseException:
        dst.unlink(missing_ok=True)
        raise


def convert_pdf(src: Path, dst: Path, target: str) -> list[Path]:
    if target == "txt":
        run(["pdftotext", "-layout", "-enc", "UTF-8", str(src), str(dst)])
        return [dst]
    prefix = dst.with_suffix("")
    run(["pdftoppm", "-png" if target == "png" else "-jpeg", "-r", "150", str(src), str(prefix)])
    pages = sorted(prefix.parent.glob(glob.escape(prefix.name) + "-*." + target),
                   key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    if len(pages) == 1:
        pages[0].replace(dst)
        return [dst]
    return pages


def scan(paths: list[Path]) -> list[tuple[Path, str]]:
    """Supported files among `paths` (folders are opened, not recursively)."""
    found = []
    for p in paths:
        for f in sorted(p.iterdir()) if p.is_dir() else [p]:
            if f.is_file() and not f.name.startswith(".") and (ext := detect(f)):
                found.append((f, ext))
    return found


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
    return [
        RED("  █  █ ▄▀▀▀▀") + "    " + BOLD(RED("US") + TEXT("wap")) + DIM(f"  v{__version__}"),
        RED("  █  █ ▀▀▀▀▄") + "    " + DIM("convert any file, right here"),
        RED("  ▀▄▄▀ ▄▄▄▄▀"),
        RED("  ─────────►"),
        AMBER("  ◄─────────"),
    ]


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
    width = max(len(label) for label, _ in items)
    items = [(label.ljust(width), hint) for label, hint in items]
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
        k = getkey()
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


def missing_hint(ext: str) -> str:
    tool = {"pdf": "Poppler"}.get(ext) or ("Pandoc" if FORMATS[ext][0] == DOC else "FFmpeg")
    return f"{tool} is not installed. Run  uswap --doctor  to see how to get it."


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
        screen(*info, "", RED("  ✘ " + missing_hint(ext)))
        pause()
        return 1
    pick = choose([*info, "", AMBER("  convert to"), ""],
                  [(t.upper().ljust(5), FORMATS[t][1]) for t in targets])
    if pick is None:
        return 130
    target = targets[pick]
    screen(*info, "")
    started = time.time()
    try:
        bar(0, f"{path.name}  ►  {target.upper()}")
        made = convert(path, ext, target, lambda f: bar(f, f"{path.name}  ►  {target.upper()}"))
    except Failed as exc:
        out("", "", RED("  ✘ conversion failed"), *(DIM("    " + line) for line in str(exc).splitlines()))
        pause()
        return 1
    bar(1, f"{path.name}  ►  {target.upper()}")
    out("", "", OK(f"  ✔ done in {time.time() - started:.1f}s"))
    for f in made[:5]:
        out(DIM("    " + str(f)))
    if len(made) > 5:
        out(DIM(f"    ...and {len(made) - 5} more"))
    pause(2.5)
    return 0


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
                      [(PLURAL[c].ljust(12), f"{len(groups[c])} files") for c in cats])
        if pick is None:
            return 130
        cats = [cats[pick]]
    files = groups[cats[0]]
    options = []
    for t in TARGETS[cats[0]]:
        if any(t in targets_for(ext) for _, ext in files):
            options.append(t)
    if not options:
        screen(RED("  ✘ " + missing_hint(files[0][1])))
        return 1
    pick = choose([f"  {BOLD(TEXT(str(len(files))))} {CATEGORY_COLOR[cats[0]](PLURAL[cats[0]])}",
                   "", AMBER("  convert all to"), ""],
                  [(t.upper().ljust(5), FORMATS[t][1]) for t in options])
    if pick is None:
        return 130
    target = options[pick]
    screen(AMBER(f"  converting {len(files)} files to {target.upper()}"), "")
    ok = skipped = failed = 0
    for f, ext in files:
        if ext == target or target not in targets_for(ext):
            skipped += 1
            out(f"  {DIM('·  skip  ' + f.name)}")
            continue
        try:
            label = f"{f.name}  ►  {target.upper()}"
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


def menu() -> int:
    while True:
        pick = choose([], [("Convert a file", "pick one file and a format"),
                           ("Convert a folder", "batch: every file of a kind at once"),
                           ("Check tools", "what is installed"),
                           ("Quit", "")], keys="↑↓ move   Enter select   q quit")
        if pick == 0 and (f := browse(Path.cwd())):
            convert_one(f)
        elif pick == 1 and (d := browse(Path.cwd(), want_folder=True)):
            if convert_many(scan([d])) != 130:
                pause()
        elif pick == 2:
            screen()
            doctor()
            pause()
        elif pick in (3, None):
            return 0


# ------------------------------------------------------------------------- CLI
def doctor() -> int:
    install = ("winget install Gyan.FFmpeg JohnMacFarlane.Pandoc oschwartz10612.Poppler"
               if WINDOWS else "sudo apt install ffmpeg pandoc poppler-utils   (or your distro's)")
    missing = 0
    for tool, use in TOOLS.items():
        found = has(tool)
        missing += not found
        out(f"  {OK('✔') if found else RED('✘')}  {TEXT(tool.ljust(10))} {DIM(use)}")
    if missing:
        out("", DIM("  to install what is missing:"), AMBER("    " + install))
    return 1 if missing else 0


def list_formats() -> None:
    for cat in (IMAGE, AUDIO, VIDEO, DOC):
        exts = [e for e, (c, _) in FORMATS.items() if c == cat]
        out(f"  {CATEGORY_COLOR[cat](cat.ljust(9))} {TEXT(' '.join(exts))}")
    out("", DIM("  images ↔ images, audio ↔ audio, video → video or audio,"),
        DIM("  documents ↔ documents, pdf → txt / png / jpg"))


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


def headless(paths: list[Path], target: str) -> int:
    target = norm(target)
    if target not in FORMATS:
        out(RED(f"  ✘ unknown format: {target}   (see uswap --formats)"))
        return 2
    failed = 0
    named = {p for p in paths if p.is_file()}  # files inside folders are skipped quietly
    for f, ext in scan(paths):
        if ext == target or (f not in named and target not in
                                    (PDF_TARGETS if ext == "pdf" else TARGETS[FORMATS[ext][0]])):
            continue
        if target not in targets_for(ext):
            why = missing_hint(ext) if not targets_for(ext) else f"cannot go from {ext} to {target}"
            out(f"{RED('✘')} {f.name}: {why}")
            failed += 1
            continue
        try:
            for made in convert(f, ext, target):
                out(f"{OK('✔')} {f.name} → {made}")
        except Failed as exc:
            out(f"{RED('✘')} {f.name}: {last(exc)}")
            failed += 1
    return 1 if failed else 0


def setup_console() -> None:
    if getattr(sys, "frozen", False):  # Windows installer: bundled tools live in .\tools
        tools = Path(sys.executable).parent / "tools"
        os.environ["PATH"] = f"{tools}{os.pathsep}{os.environ.get('PATH', '')}"
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
    ap.add_argument("--formats", action="store_true", help="list supported formats")
    ap.add_argument("--doctor", action="store_true", help="check FFmpeg, Pandoc and Poppler")
    ap.add_argument("-V", "--version", action="version", version=f"USwap {__version__}")
    args = ap.parse_args(argv)

    if args.formats:
        list_formats()
        return 0
    if args.doctor:
        return doctor()
    paths = expand(args.files)
    if args.files and not paths:
        return 2
    if args.to:
        return headless(paths, args.to)
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        out("USwap needs an interactive terminal here. Use --to FMT for scripts.")
        return 2
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
