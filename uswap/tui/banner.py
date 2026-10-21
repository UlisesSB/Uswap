"""ANSI isotype + banner renderer."""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.text import Text

from uswap import __version__
from uswap.tui.theme import UI
from uswap.utils.i18n import t

_UNICODE_ART = [
    "╭─────────────╮",
    "│  █  █ █▀▀▀  │",
    "│  █  █ ▀▀▀█  │",
    "│  ▀▄▄▀ █▄▄█  │",
    "│      ⇄      │",
    "╰─────────────╯",
]
_ASCII_ART = [
    "+-------------+",
    "|  #  # ####  |",
    "|  #  # ###   |",
    "|  ####    #  |",
    "|     <>      |",
    "+-------------+",
]


def isotype_lines(ascii_mode: bool = False) -> list[str]:
    return list(_ASCII_ART if ascii_mode else _UNICODE_ART)


def render_banner(ui: UI, compact: bool = False) -> RenderableType:
    """Isotype on the left, product info on the right."""
    th = ui.theme
    if compact:
        line = Text()
        line.append(f" {ui.g.swap} ", style=f"bold {th.brand}")
        line.append("USwap", style=f"bold {th.brand}")
        line.append(f" v{__version__}", style=th.dim)
        return line

    art = isotype_lines(ui.ascii)
    info = [
        ("", ""),
        (f"USwap v{__version__}", f"bold {th.fg}"),
        (t("banner.tagline"), th.dim),
        ("─" * 32 if not ui.ascii else "-" * 32, th.border),
        (t("banner.command"), th.dim),
        ("", ""),
    ]
    rows = []
    for left, (right, style) in zip(art, info, strict=False):
        row = Text()
        row.append(left, style=th.brand)
        row.append("   ")
        row.append(right, style=style)
        rows.append(row)
    return Group(*rows)
