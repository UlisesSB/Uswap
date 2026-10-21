"""Dependency inspector: which engines are available on this machine?"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"


def add_bundled_tools_to_path() -> Path | None:
    """In the packaged Windows build, FFmpeg/Pandoc/Poppler live in ``<app>\\tools``.

    Prepending that folder to PATH lets every engine find them with ``shutil.which``.
    Returns the folder that was added (None when not running a packaged build).
    """
    if not getattr(sys, "frozen", False):
        return None
    tools = Path(sys.executable).resolve().parent / "tools"
    if tools.is_dir():
        current = os.environ.get("PATH", "")
        if str(tools) not in current.split(os.pathsep):
            os.environ["PATH"] = str(tools) + os.pathsep + current
        return tools
    return None


add_bundled_tools_to_path()


@dataclass(frozen=True)
class Dependency:
    name: str
    kind: str  # "python" | "binary"
    required: bool
    available: bool
    version: str = ""
    purpose: str = ""  # i18n key suffix, see locales "dep.<purpose>"


def subprocess_flags() -> dict:
    """Extra ``subprocess`` kwargs (hide console flashes on Windows)."""
    if IS_WINDOWS:
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


def _binary_version(binary: str, flag: str = "-version") -> str:
    path = shutil.which(binary)
    if not path:
        return ""
    try:
        out = subprocess.run(
            [path, flag], capture_output=True, text=True, timeout=5, **subprocess_flags()
        )
        first = (out.stdout or out.stderr).strip().splitlines()
        if not first:
            return ""
        match = re.search(r"\d+(?:\.\d+)+\S*", first[0])
        return match.group(0) if match else first[0][:40]
    except (OSError, subprocess.SubprocessError):
        return ""


def has_binary(name: str) -> bool:
    return shutil.which(name) is not None


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


@lru_cache(maxsize=1)
def check_all() -> tuple[Dependency, ...]:
    pillow_version = ""
    if has_module("PIL"):
        try:
            import PIL

            pillow_version = PIL.__version__
        except Exception:  # pragma: no cover
            pass
    return (
        Dependency("pillow", "python", True, has_module("PIL"), pillow_version, "image"),
        Dependency("watchdog", "python", True, has_module("watchdog"), "", "watcher"),
        Dependency("rich", "python", True, has_module("rich"), "", "ui"),
        Dependency(
            "ffmpeg", "binary", False, has_binary("ffmpeg"), _binary_version("ffmpeg"), "media"
        ),
        Dependency(
            "pandoc",
            "binary",
            False,
            has_binary("pandoc"),
            _binary_version("pandoc", "--version"),
            "document",
        ),
        Dependency(
            "pdftoppm",
            "binary",
            False,
            has_binary("pdftoppm"),
            _binary_version("pdftoppm", "-v"),
            "pdf",
        ),
        Dependency("pdftotext", "binary", False, has_binary("pdftotext"), "", "pdf"),
    )


def engine_available(engine: str) -> bool:
    """``engine`` is one of: image, media, pandoc, poppler."""
    if engine == "image":
        return has_module("PIL")
    if engine == "media":
        return has_binary("ffmpeg")
    if engine == "pandoc":
        return has_binary("pandoc")
    if engine == "poppler":
        return has_binary("pdftoppm") and has_binary("pdftotext")
    return False


def clear_cache() -> None:
    check_all.cache_clear()
