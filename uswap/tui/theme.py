"""Color themes, glyph sets and the shared :class:`UI` context."""

from __future__ import annotations

from dataclasses import dataclass

from rich import box
from rich.console import Console

from uswap.utils.config import Config


@dataclass(frozen=True)
class Theme:
    name: str
    brand: str  # the "red" of the brand, adapted to each palette
    accent: str
    fg: str
    dim: str
    ok: str
    warn: str
    err: str
    border: str
    sel_fg: str


THEMES: dict[str, Theme] = {
    "gruvbox": Theme(
        "gruvbox",
        "#fb4934",
        "#fabd2f",
        "#ebdbb2",
        "#928374",
        "#b8bb26",
        "#fe8019",
        "#fb4934",
        "#665c54",
        "#282828",
    ),
    "nord": Theme(
        "nord",
        "#bf616a",
        "#88c0d0",
        "#d8dee9",
        "#7b88a1",
        "#a3be8c",
        "#ebcb8b",
        "#bf616a",
        "#4c566a",
        "#2e3440",
    ),
    "catppuccin": Theme(
        "catppuccin",
        "#f38ba8",
        "#cba6f7",
        "#cdd6f4",
        "#7f849c",
        "#a6e3a1",
        "#f9e2af",
        "#f38ba8",
        "#45475a",
        "#1e1e2e",
    ),
    "tokyo-night": Theme(
        "tokyo-night",
        "#f7768e",
        "#7aa2f7",
        "#c0caf5",
        "#565f89",
        "#9ece6a",
        "#e0af68",
        "#f7768e",
        "#3b4261",
        "#1a1b26",
    ),
    "monokai": Theme(
        "monokai",
        "#f92672",
        "#a6e22e",
        "#f8f8f2",
        "#75715e",
        "#a6e22e",
        "#e6db74",
        "#f92672",
        "#49483e",
        "#272822",
    ),
}


@dataclass(frozen=True)
class Glyphs:
    cursor: str
    ok: str
    fail: str
    dot: str
    dir: str
    up: str
    swap: str
    ellipsis: str


UNICODE = Glyphs("❯", "✔", "✘", "•", "▸", "↑", "⇄", "…")
ASCII = Glyphs(">", "v", "x", "*", "+", "^", "<>", "...")


class UI:
    """Bundle of console + theme + glyphs passed to every screen."""

    def __init__(self, console: Console, theme: Theme, glyphs: Glyphs, ascii_mode: bool):
        self.console = console
        self.theme = theme
        self.g = glyphs
        self.ascii = ascii_mode
        self.box = box.ASCII if ascii_mode else box.ROUNDED

    @classmethod
    def from_config(cls, config: Config, console: Console | None = None) -> UI:
        console = console or Console()
        theme = THEMES.get(str(config.get("theme", "gruvbox")), THEMES["gruvbox"])
        ascii_mode = config.get("glyphs", "unicode") == "ascii"
        return cls(console, theme, ASCII if ascii_mode else UNICODE, ascii_mode)

    def reload(self, config: Config) -> None:
        """Apply theme/glyph changes without rebuilding the console."""
        self.theme = THEMES.get(str(config.get("theme", "gruvbox")), THEMES["gruvbox"])
        self.ascii = config.get("glyphs", "unicode") == "ascii"
        self.g = ASCII if self.ascii else UNICODE
        self.box = box.ASCII if self.ascii else box.ROUNDED

    @property
    def width(self) -> int:
        return self.console.size.width

    @property
    def height(self) -> int:
        return self.console.size.height

    # style helpers --------------------------------------------------------
    @property
    def sel_style(self) -> str:
        return f"bold {self.theme.sel_fg} on {self.theme.accent}"
