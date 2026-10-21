#!/usr/bin/env python3
"""Generate the USwap logo assets (PNG + ICO) with Pillow.

    python scripts/make_assets.py

Outputs (in ``assets/``): logo.png, logo-mark.png, banner.png, uswap.ico.
The glyphs are drawn from a tiny pixel font so no font files are needed.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

RED = (225, 29, 46, 255)  # #E11D2E - the brand color
WHITE = (255, 255, 255, 255)
OUT = Path(__file__).resolve().parent.parent / "assets"

# 5-wide pixel glyphs. Capitals are 7 rows, lowercase x-height is 5 rows.
GLYPHS = {
    "U": ["X...X", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "S": [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."],
    "w": ["X...X", "X...X", "X.X.X", "XX.XX", "X...X"],
    "a": [".XXX.", "....X", ".XXXX", "X...X", ".XXXX"],
    "p": ["XXXX.", "X...X", "X...X", "X...X", "XXXX.", "X....", "X...."],
}
LOWER = {"w", "a", "p"}


def draw_glyph(d: ImageDraw.ImageDraw, ch: str, x: int, y: int, cell: int, fill) -> int:
    """Draw ``ch`` with its top-left at (x, y) where y is the cap-line. Returns width in px."""
    rows = GLYPHS[ch]
    y0 = y + (2 * cell if ch in LOWER else 0)
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if v == "X":
                d.rectangle(
                    [x + c * cell, y0 + r * cell, x + (c + 1) * cell - 1, y0 + (r + 1) * cell - 1],
                    fill=fill,
                )
    return len(rows[0]) * cell


def word(d, text: str, x: int, y: int, cell: int, fill) -> int:
    cur = x
    for ch in text:
        cur += draw_glyph(d, ch, cur, y, cell, fill) + cell
    return cur - cell - x


def word_width(text: str, cell: int) -> int:
    return sum(5 * cell + cell for _ in text) - cell


def arrows(d, cx: int, y: int, width: int, thick: int, fill) -> None:
    """Draw the swap symbol: two stacked horizontal arrows pointing opposite ways."""
    half = width // 2
    head = thick * 2
    gap = thick * 2
    # top: left -> right
    ty = y
    d.rectangle([cx - half, ty - thick // 2, cx + half - head, ty + thick // 2], fill=fill)
    d.polygon(
        [(cx + half, ty), (cx + half - head, ty - head), (cx + half - head, ty + head)], fill=fill
    )
    # bottom: right -> left
    by = y + head + gap
    d.rectangle([cx - half + head, by - thick // 2, cx + half, by + thick // 2], fill=fill)
    d.polygon(
        [(cx - half, by), (cx - half + head, by - head), (cx - half + head, by + head)], fill=fill
    )


def isotype(size: int, *, bg: bool) -> Image.Image:
    """The square mark: ``US`` blocks + swap arrows. bg=True -> white on red tile."""
    scale = 4  # supersample for smooth edges
    S = size * scale
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fg = WHITE if bg else RED
    if bg:
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=RED)
    else:
        w = int(S * 0.035)
        d.rounded_rectangle(
            [w // 2, w // 2, S - 1 - w // 2, S - 1 - w // 2],
            radius=int(S * 0.22),
            outline=RED,
            width=w,
        )

    cell = int(S * 0.056)
    total_w = word_width("US", cell)
    x = (S - total_w) // 2
    y = int(S * 0.19)
    word(d, "US", x, y, cell, fg)
    arrows(d, S // 2, int(S * 0.69), total_w, max(int(cell * 0.5), 2), fg)
    return img.resize((size, size), Image.LANCZOS)


def banner() -> Image.Image:
    h = 280
    cell = 22
    text = "USwap"
    tw = word_width(text, cell)
    pad = 40
    W = pad + h + 56 + tw + pad
    scale = 2
    img = Image.new("RGBA", (W * scale, h * scale), (0, 0, 0, 0))
    big_mark = isotype(h * scale, bg=False)
    img.paste(big_mark, (pad * scale, 0), big_mark)
    d = ImageDraw.Draw(img)
    text_h = 9 * cell * scale  # cap height 7 rows + 2 descender rows
    word(d, text, (pad + h + 56) * scale, (h * scale - text_h) // 2, cell * scale, RED)
    return img.resize((W, h), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    logo = isotype(512, bg=True)
    logo.save(OUT / "logo.png")
    isotype(512, bg=False).save(OUT / "logo-mark.png")
    banner().save(OUT / "banner.png")
    logo.save(
        OUT / "uswap.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("assets written to", OUT)


if __name__ == "__main__":
    main()
