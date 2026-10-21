"""Magic-byte file type detector.

The extension is only a *hint*: the first bytes of the file decide the type
(e.g. a PNG renamed to ``photo.jpg`` is still treated as PNG). Text based
formats (Markdown, plain text) cannot be identified by magic bytes, so for
those the extension is trusted as long as the file looks like text.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from uswap.core import formats
from uswap.utils import system

HEAD_BYTES = 4096


@dataclass
class FileInfo:
    path: Path
    size: int = 0
    declared_ext: str = ""  # normalized extension from the file name
    ext: str = ""  # detected format ("" when unsupported)
    mime: str = "application/octet-stream"
    category: str | None = None
    verified: bool = False  # True when decided by magic bytes / content
    mismatch: bool = False  # extension disagrees with the real content
    error: str = ""
    targets: list[str] = field(default_factory=list)  # filled by targets_for()

    @property
    def supported(self) -> bool:
        return bool(self.ext) and not self.error

    @property
    def label(self) -> str:
        return formats.label_of(self.ext) if self.ext else "unknown"


def _riff_type(head: bytes) -> str | None:
    kind = head[8:12]
    if kind == b"WEBP":
        return "webp"
    if kind == b"WAVE":
        return "wav"
    if kind == b"AVI ":
        return "avi"
    return None


def _ogg_type(head: bytes) -> str:
    return "opus" if b"OpusHead" in head[:128] else "ogg"


def _mp4_type(head: bytes) -> str | None:
    if head[4:8] != b"ftyp":
        return None
    brand = head[8:12]
    if brand == b"qt  ":
        return "mov"
    if brand in (b"M4A ", b"M4B ", b"M4P "):
        return "m4a"
    return "mp4"


def _matroska_type(head: bytes) -> str:
    return "webm" if b"webm" in head[:64] else "mkv"


def _zip_type(path: Path) -> str | None:
    try:
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            if "word/document.xml" in names:
                return "docx"
            if "mimetype" in names:
                mt = zf.read("mimetype")[:100].strip()
                if mt == b"application/vnd.oasis.opendocument.text":
                    return "odt"
                if mt == b"application/epub+zip":
                    return "epub"
    except (zipfile.BadZipFile, OSError, KeyError):
        pass
    return None


def sniff(path: Path, head: bytes) -> str | None:
    """Return the detected format from magic bytes, or None."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head.startswith(b"BM") and len(head) > 14:
        return "bmp"
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if head.startswith(b"\x00\x00\x01\x00"):
        return "ico"
    if head.startswith(b"RIFF") and len(head) >= 12:
        return _riff_type(head)
    if head.startswith(b"fLaC"):
        return "flac"
    if head.startswith(b"OggS"):
        return _ogg_type(head)
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return _matroska_type(head)
    mp4 = _mp4_type(head)
    if mp4:
        return mp4
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"{\\rtf"):
        return "rtf"
    if head.startswith(b"PK\x03\x04"):
        return _zip_type(path)
    if len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xF6) == 0xF0:
        return "aac"  # ADTS frame header
    if head.startswith(b"ID3"):
        return "mp3"
    if (
        len(head) >= 2
        and head[0] == 0xFF
        and (head[1] & 0xE0) == 0xE0
        and ((head[1] >> 1) & 3) != 0
    ):
        return "mp3"  # MPEG audio frame sync
    stripped = head.lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if stripped.startswith((b"<!doctype html", b"<html")):
        return "html"
    return None


def _looks_like_text(head: bytes) -> bool:
    if b"\x00" in head:
        return False
    try:
        head.decode("utf-8")
        return True
    except UnicodeDecodeError:
        # A multibyte char may be cut at the end of the sample.
        try:
            head[:-3].decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False


def detect(path: str | Path) -> FileInfo:
    """Inspect ``path`` and return a :class:`FileInfo` (never raises)."""
    path = Path(path)
    info = FileInfo(path=path, declared_ext=formats.normalize_ext(path.suffix))
    try:
        if not path.is_file():
            info.error = "not_a_file"
            return info
        info.size = path.stat().st_size
        with path.open("rb") as fh:
            head = fh.read(HEAD_BYTES)
    except OSError as exc:
        info.error = f"io:{exc.strerror or exc}"
        return info

    detected = sniff(path, head)
    declared = info.declared_ext
    if detected:
        info.ext, info.verified = detected, True
        # html/rtf sniffing is weak for look-alikes; md/txt declared + html content -> html
        info.mismatch = (
            bool(declared)
            and declared != detected
            and not (declared in ("md", "txt") and detected == "html")
        )
    elif declared in ("md", "txt", "html") and _looks_like_text(head):
        info.ext, info.verified = declared, True
    elif declared in formats.FORMATS and declared not in ("md", "txt", "html"):
        if _looks_like_text(head):
            info.error = "unsupported"  # e.g. a text file renamed to .png
        else:
            # Binary format we could not verify (e.g. odd header): trust the extension.
            info.ext, info.verified = declared, False
    else:
        info.error = "unsupported"

    if info.ext:
        info.mime = formats.mime_of(info.ext)
        info.category = formats.category_of(info.ext)
        info.targets = targets_for(info)
    return info


def targets_for(info: FileInfo | str, available_only: bool = True) -> list[str]:
    """Output formats for a file, optionally limited to installed engines."""
    ext = info.ext if isinstance(info, FileInfo) else formats.normalize_ext(info)
    result = []
    for target in formats.all_targets(ext):
        engine = formats.engine_for(ext, target)
        if engine and (not available_only or system.engine_available(engine)):
            result.append(target)
    return result


def is_supported(path: str | Path) -> bool:
    return detect(path).supported


def common_targets(infos: list[FileInfo]) -> list[str]:
    """Targets valid for *every* file in ``infos`` (order of the first file)."""
    if not infos:
        return []
    common = list(infos[0].targets)
    for info in infos[1:]:
        common = [t for t in common if t in info.targets]
    return common
