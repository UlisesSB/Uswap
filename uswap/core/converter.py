"""High level conversion: output naming + engine dispatch."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from uswap.core import detector, engine_doc, engine_image, engine_media, formats
from uswap.core.errors import Cancelled, ConversionError, MissingDependency
from uswap.utils.config import Config


@dataclass
class ConversionResult:
    src: Path
    target: str
    ok: bool
    outputs: list[Path] = field(default_factory=list)
    error: str = ""
    elapsed: float = 0.0
    skipped: bool = False


def unique_path(path: Path) -> Path:
    """``name.ext`` -> ``name (1).ext`` ... until the path is free."""
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def resolve_output(src: Path, target: str, config: Config) -> Path:
    """Apply the output-directory and naming rules from the configuration."""
    out_dir = config.output_dir_for(src)
    naming = config.get("output.naming", "keep")
    suffix = str(config.get("output.suffix", "-converted"))
    stem = src.stem + (suffix if naming == "suffix" else "")
    dst = out_dir / f"{stem}.{target}"
    try:
        same_file = dst.resolve() == src.resolve()
    except OSError:
        same_file = dst == src
    if same_file:  # never clobber the source
        dst = out_dir / f"{src.stem}{suffix or '-converted'}.{target}"
    if naming != "overwrite":
        dst = unique_path(dst)
    return dst


def convert_file(
    src: str | Path,
    target: str,
    config: Config,
    *,
    info: detector.FileInfo | None = None,
    progress: Callable[[float], None] | None = None,
    cancel: threading.Event | None = None,
) -> ConversionResult:
    """Convert ``src`` to ``target``. Never raises: errors land in the result."""
    src = Path(src)
    started = time.monotonic()
    target = formats.normalize_ext(target)

    def fail(message: str) -> ConversionResult:
        return ConversionResult(
            src, target, False, error=message, elapsed=time.monotonic() - started
        )

    info = info or detector.detect(src)
    if not info.supported:
        return fail(f"unsupported:{info.error or 'unknown'}")
    if target == info.ext:
        return ConversionResult(src, target, True, [src], skipped=True, elapsed=0.0)
    engine = formats.engine_for(info.ext, target)
    if engine is None:
        return fail(f"no_route:{info.ext}->{target}")

    dst = resolve_output(src, target, config)
    try:
        if engine == "image":
            outputs = engine_image.convert(
                src, dst, target, quality=int(config.get("quality.image", 90)), progress=progress
            )
        elif engine == "media":
            outputs = engine_media.convert(src, dst, target, progress=progress, cancel=cancel)
        else:  # pandoc / poppler
            outputs = engine_doc.convert(
                src, dst, info.ext, target, progress=progress, cancel=cancel
            )
    except MissingDependency as exc:
        return fail(f"missing:{exc.tool}")
    except Cancelled:
        return fail("cancelled")
    except ConversionError as exc:
        return fail(str(exc))
    except Exception as exc:  # defensive: engines must not crash the UI
        return fail(f"{type(exc).__name__}: {exc}")
    return ConversionResult(src, target, True, outputs, elapsed=time.monotonic() - started)


def format_error(error: str, t: Callable[..., str]) -> str:
    """Translate the machine-readable errors produced by :func:`convert_file`."""
    kind, _, detail = error.partition(":")
    if kind == "missing":
        return t("err.missing_dep", tool=detail)
    if kind == "unsupported":
        return t("err.unsupported")
    if kind == "no_route":
        return t("err.no_route", route=detail)
    if kind == "cancelled":
        return t("err.cancelled")
    return error
