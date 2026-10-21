"""Document engine (Pandoc for text documents, Poppler for PDF)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from uswap.core.errors import ConversionError, MissingDependency
from uswap.utils.system import subprocess_flags

PANDOC_READER = {
    "md": "markdown",
    "txt": "markdown",
    "html": "html",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "epub": "epub",
}
PANDOC_WRITER = {
    "md": "gfm",
    "txt": "plain",
    "html": "html5",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "epub": "epub",
}


def _run(cmd: list[str], cancel: threading.Event | None) -> None:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        **subprocess_flags(),
    )
    try:
        while True:
            try:
                _, err = proc.communicate(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                if cancel is not None and cancel.is_set():
                    proc.kill()
                    proc.wait()
                    raise ConversionError("cancelled") from None
    except BaseException:
        proc.kill()
        raise
    if proc.returncode != 0:
        raise ConversionError((err or "").strip() or f"{Path(cmd[0]).name} failed")


def _pandoc(src: Path, dst: Path, source_ext: str, target: str, cancel) -> list[Path]:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise MissingDependency("pandoc")
    cmd = [
        pandoc,
        str(src),
        "-f",
        PANDOC_READER[source_ext],
        "-t",
        PANDOC_WRITER[target],
        "-o",
        str(dst),
    ]
    if target == "html":
        cmd += ["-s", "--metadata", f"title={src.stem}"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run(cmd, cancel)
    except ConversionError:
        dst.unlink(missing_ok=True)
        raise
    return [dst]


def _poppler(src: Path, dst: Path, target: str, cancel) -> list[Path]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if target == "txt":
        tool = shutil.which("pdftotext")
        if not tool:
            raise MissingDependency("pdftotext")
        try:
            _run([tool, "-layout", "-enc", "UTF-8", str(src), str(dst)], cancel)
        except ConversionError:
            dst.unlink(missing_ok=True)
            raise
        return [dst]

    tool = shutil.which("pdftoppm")
    if not tool:
        raise MissingDependency("pdftoppm")
    flag = "-png" if target == "png" else "-jpeg"
    tmp = Path(tempfile.mkdtemp(prefix=".uswap-", dir=dst.parent))
    try:
        _run([tool, flag, "-r", "150", str(src), str(tmp / "page")], cancel)
        pages = sorted(tmp.glob(f"page-*.{target if target == 'png' else 'jpg'}"))
        if not pages:
            raise ConversionError("no pages were rendered")
        if len(pages) == 1:
            pages[0].replace(dst)
            return [dst]
        outputs = []
        for page in pages:
            number = page.stem.split("-")[-1]
            final = dst.with_name(f"{dst.stem}-{number}{dst.suffix}")
            page.replace(final)
            outputs.append(final)
        return outputs
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def convert(
    src: Path,
    dst: Path,
    source_ext: str,
    target: str,
    *,
    progress: Callable[[float], None] | None = None,
    cancel: threading.Event | None = None,
) -> list[Path]:
    if progress:
        progress(0.1)
    if source_ext == "pdf":
        result = _poppler(src, dst, target, cancel)
    elif source_ext in PANDOC_READER and target in PANDOC_WRITER:
        result = _pandoc(src, dst, source_ext, target, cancel)
    else:
        raise ConversionError(f"unsupported document conversion: {source_ext} -> {target}")
    if progress:
        progress(1.0)
    return result
