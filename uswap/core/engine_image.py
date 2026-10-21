"""Image engine (Pillow)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from uswap.core.errors import ConversionError, MissingDependency

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]

PIL_FORMAT = {
    "png": "PNG",
    "jpg": "JPEG",
    "webp": "WEBP",
    "bmp": "BMP",
    "gif": "GIF",
    "tiff": "TIFF",
    "ico": "ICO",
    "pdf": "PDF",
}
ICO_SIZES = (16, 32, 48, 64, 128, 256)


def _flatten(img: Image.Image) -> Image.Image:
    """Return an RGB image, compositing transparency over white."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.getchannel("A"))
        return bg
    return img.convert("RGB")


def convert(
    src: Path,
    dst: Path,
    target: str,
    *,
    quality: int = 90,
    progress: Callable[[float], None] | None = None,
) -> list[Path]:
    if Image is None:
        raise MissingDependency("pillow")
    if target not in PIL_FORMAT:
        raise ConversionError(f"unsupported image target: {target}")
    if progress:
        progress(0.05)
    try:
        with Image.open(src) as img:
            animated = bool(getattr(img, "is_animated", False)) and target in ("gif", "webp")
            if not animated:
                img = ImageOps.exif_transpose(img)
            kwargs: dict = {}
            if target == "jpg":
                out = _flatten(img)
                kwargs = {"quality": int(quality), "optimize": True}
            elif target == "png":
                out = (
                    img if img.mode in ("RGB", "RGBA", "L", "LA", "P", "1") else img.convert("RGBA")
                )
                kwargs = {"optimize": True}
            elif target == "webp":
                out = (
                    img
                    if animated
                    else (img if img.mode in ("RGB", "RGBA") else img.convert("RGBA"))
                )
                kwargs = {"quality": int(quality), "method": 4}
                if animated:
                    kwargs.update(save_all=True)
            elif target == "gif":
                out = img
                if animated:
                    kwargs = {"save_all": True, "loop": img.info.get("loop", 0)}
            elif target == "bmp":
                out = img if img.mode in ("RGB", "L", "P", "1") else _flatten(img)
            elif target == "tiff":
                out = img if img.mode in ("RGB", "RGBA", "L", "CMYK") else img.convert("RGBA")
                kwargs = {"compression": "tiff_lzw"}
            elif target == "ico":
                out = img.convert("RGBA")
                sizes = [(s, s) for s in ICO_SIZES if s <= max(out.size)] or [(16, 16)]
                kwargs = {"sizes": sizes}
            else:  # pdf
                out = _flatten(img)
                kwargs = {"resolution": 100.0}
            if progress:
                progress(0.4)
            dst.parent.mkdir(parents=True, exist_ok=True)
            out.save(dst, format=PIL_FORMAT[target], **kwargs)
    except UnidentifiedImageError as exc:
        raise ConversionError(f"cannot read image: {exc}") from exc
    except (OSError, ValueError) as exc:
        dst.unlink(missing_ok=True)
        raise ConversionError(str(exc)) from exc
    if progress:
        progress(1.0)
    return [dst]
