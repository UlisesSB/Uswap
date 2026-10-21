"""Format registry: extensions, MIME types, categories and conversion targets."""

from __future__ import annotations

from dataclasses import dataclass

IMAGE, AUDIO, VIDEO, DOCUMENT = "image", "audio", "video", "document"
CATEGORIES = (IMAGE, AUDIO, VIDEO, DOCUMENT)


@dataclass(frozen=True)
class Fmt:
    ext: str
    category: str
    mime: str
    label: str


_FORMATS = [
    # images
    Fmt("png", IMAGE, "image/png", "PNG image"),
    Fmt("jpg", IMAGE, "image/jpeg", "JPEG image"),
    Fmt("webp", IMAGE, "image/webp", "WebP image"),
    Fmt("gif", IMAGE, "image/gif", "GIF image"),
    Fmt("bmp", IMAGE, "image/bmp", "BMP image"),
    Fmt("tiff", IMAGE, "image/tiff", "TIFF image"),
    Fmt("ico", IMAGE, "image/vnd.microsoft.icon", "Windows icon"),
    # audio
    Fmt("mp3", AUDIO, "audio/mpeg", "MP3 audio"),
    Fmt("wav", AUDIO, "audio/wav", "WAV audio"),
    Fmt("flac", AUDIO, "audio/flac", "FLAC audio"),
    Fmt("ogg", AUDIO, "audio/ogg", "Ogg Vorbis audio"),
    Fmt("opus", AUDIO, "audio/opus", "Opus audio"),
    Fmt("aac", AUDIO, "audio/aac", "AAC audio"),
    Fmt("m4a", AUDIO, "audio/mp4", "M4A audio"),
    # video
    Fmt("mp4", VIDEO, "video/mp4", "MP4 video"),
    Fmt("mkv", VIDEO, "video/x-matroska", "Matroska video"),
    Fmt("webm", VIDEO, "video/webm", "WebM video"),
    Fmt("avi", VIDEO, "video/x-msvideo", "AVI video"),
    Fmt("mov", VIDEO, "video/quicktime", "QuickTime video"),
    # documents
    Fmt("pdf", DOCUMENT, "application/pdf", "PDF document"),
    Fmt(
        "docx",
        DOCUMENT,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Word document",
    ),
    Fmt("odt", DOCUMENT, "application/vnd.oasis.opendocument.text", "OpenDocument text"),
    Fmt("rtf", DOCUMENT, "application/rtf", "Rich Text Format"),
    Fmt("epub", DOCUMENT, "application/epub+zip", "EPUB e-book"),
    Fmt("html", DOCUMENT, "text/html", "HTML document"),
    Fmt("md", DOCUMENT, "text/markdown", "Markdown text"),
    Fmt("txt", DOCUMENT, "text/plain", "Plain text"),
]

FORMATS: dict[str, Fmt] = {f.ext: f for f in _FORMATS}

ALIASES = {
    "jpeg": "jpg",
    "jpe": "jpg",
    "jfif": "jpg",
    "tif": "tiff",
    "htm": "html",
    "markdown": "md",
    "mdown": "md",
    "text": "txt",
    "log": "txt",
    "oga": "ogg",
    "mp2": "mp3",
    "m4v": "mp4",
    "qt": "mov",
}

# Output formats offered per *source* category.
TARGETS: dict[str, list[str]] = {
    IMAGE: ["png", "jpg", "webp", "bmp", "gif", "tiff", "ico", "pdf"],
    AUDIO: ["mp3", "wav", "flac", "ogg", "opus", "aac", "m4a"],
    # video targets include "audio extraction" formats
    VIDEO: [
        "mp4",
        "mkv",
        "webm",
        "avi",
        "mov",
        "gif",
        "mp3",
        "wav",
        "flac",
        "ogg",
        "opus",
        "aac",
        "m4a",
    ],
    DOCUMENT: ["md", "txt", "html", "docx", "odt", "rtf", "epub"],
}
PDF_TARGETS = ["txt", "png", "jpg"]  # PDF is read through Poppler


def normalize_ext(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    return ALIASES.get(ext, ext)


def category_of(ext: str) -> str | None:
    fmt = FORMATS.get(normalize_ext(ext))
    return fmt.category if fmt else None


def mime_of(ext: str) -> str:
    fmt = FORMATS.get(normalize_ext(ext))
    return fmt.mime if fmt else "application/octet-stream"


def label_of(ext: str) -> str:
    fmt = FORMATS.get(normalize_ext(ext))
    return fmt.label if fmt else ext.upper()


def all_targets(source_ext: str) -> list[str]:
    """Targets that make sense for ``source_ext`` regardless of installed tools."""
    ext = normalize_ext(source_ext)
    fmt = FORMATS.get(ext)
    if not fmt:
        return []
    if ext == "pdf":
        return list(PDF_TARGETS)
    return [t for t in TARGETS[fmt.category] if t != ext]


def engine_for(source_ext: str, target: str) -> str | None:
    """Return the engine id (image|media|pandoc|poppler) handling this pair."""
    ext = normalize_ext(source_ext)
    fmt = FORMATS.get(ext)
    if not fmt or target not in all_targets(ext):
        return None
    if ext == "pdf":
        return "poppler"
    return {IMAGE: "image", AUDIO: "media", VIDEO: "media", DOCUMENT: "pandoc"}[fmt.category]
