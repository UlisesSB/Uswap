"""Reusable TUI building blocks: list view, text prompt, screen loop."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rich.console import Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from uswap.tui.keys import KeyReader
from uswap.tui.theme import UI
from uswap.utils.i18n import t

CONTINUE = object()  # sentinel: keep the screen loop running


@dataclass
class Item:
    label: str
    value: Any = None
    hint: str = ""  # right-aligned dim text
    enabled: bool = True
    style: str = ""  # optional rich style for the label
    selectable: bool = True  # False: no checkbox / cannot be toggled in multi mode


class ListView:
    """Selectable list with Vim keys, `/` search and optional multi-select."""

    def __init__(self, items: list[Item], multi: bool = False, searchable: bool = True):
        self.items = items
        self.multi = multi
        self.searchable = searchable
        self.query = ""
        self.searching = False
        self.cursor = 0  # index in the filtered list
        self.offset = 0
        self.selected: set[int] = set()  # indexes into self.items

    # -- data ------------------------------------------------------------
    @property
    def visible(self) -> list[tuple[int, Item]]:
        if not self.query:
            return list(enumerate(self.items))
        q = self.query.lower()
        return [(i, it) for i, it in enumerate(self.items) if q in it.label.lower()]

    def current(self) -> Item | None:
        vis = self.visible
        if 0 <= self.cursor < len(vis):
            return vis[self.cursor][1]
        return None

    def current_index(self) -> int | None:
        vis = self.visible
        if 0 <= self.cursor < len(vis):
            return vis[self.cursor][0]
        return None

    def selected_items(self) -> list[Item]:
        return [self.items[i] for i in sorted(self.selected)]

    def set_items(self, items: list[Item], keep_cursor: bool = False) -> None:
        old = self.cursor
        self.items = items
        self.selected = {i for i in self.selected if i < len(items)}
        self.cursor = min(old, max(len(self.visible) - 1, 0)) if keep_cursor else 0
        self.offset = 0

    def _clamp(self) -> None:
        n = len(self.visible)
        self.cursor = max(0, min(self.cursor, n - 1)) if n else 0

    # -- input -----------------------------------------------------------
    def handle(self, key: str) -> str | None:
        """Process a key. Returns ``"enter"``, ``"cancel"`` or ``None``."""
        if self.searching:
            if key == "esc":
                self.searching, self.query = False, ""
            elif key == "enter":
                self.searching = False
            elif key == "backspace":
                self.query = self.query[:-1]
            elif key == "ctrl-u":
                self.query = ""
            elif key in ("up", "down"):
                self.cursor += 1 if key == "down" else -1
            elif key == "space":
                self.query += " "
                self.cursor = 0
            elif len(key) == 1 and key.isprintable():
                self.query += key
                self.cursor = 0
            self._clamp()
            return None

        n = len(self.visible)
        if key in ("down", "j"):
            self.cursor += 1
        elif key in ("up", "k"):
            self.cursor -= 1
        elif key in ("home", "g"):
            self.cursor = 0
        elif key in ("end", "G"):
            self.cursor = n - 1
        elif key == "pgdn":
            self.cursor += 10
        elif key == "pgup":
            self.cursor -= 10
        elif key == "/" and self.searchable:
            self.searching = True
        elif key == "space" and self.multi:
            idx = self.current_index()
            if idx is not None and self.items[idx].enabled and self.items[idx].selectable:
                self.selected.symmetric_difference_update({idx})
                self.cursor += 1
        elif key == "enter":
            item = self.current()
            if item is not None and item.enabled:
                return "enter"
        elif key in ("esc", "q"):
            if self.query:
                self.query = ""
            else:
                return "cancel"
        self._clamp()
        return None

    # -- render ----------------------------------------------------------
    def render(self, ui: UI, height: int) -> RenderableType:
        th, g = ui.theme, ui.g
        vis = self.visible
        height = max(height, 3)
        if self.cursor < self.offset:
            self.offset = self.cursor
        elif self.cursor >= self.offset + height:
            self.offset = self.cursor - height + 1
        window = vis[self.offset : self.offset + height]

        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(width=1)
        if self.multi:
            grid.add_column(width=3)
        grid.add_column(ratio=1, no_wrap=True, overflow="ellipsis")
        grid.add_column(justify="right", no_wrap=True)

        for pos, (idx, item) in enumerate(window, start=self.offset):
            active = pos == self.cursor
            if not item.enabled:
                style = th.dim
            elif active:
                style = ui.sel_style
            else:
                style = item.style or th.fg
            marker = Text(g.cursor if active else " ", style=ui.sel_style if active else th.accent)
            label = Text(item.label, style=style)
            hint = Text(item.hint, style=ui.sel_style if active else th.dim)
            cells: list[Any] = [marker]
            if self.multi:
                checked = idx in self.selected
                if item.selectable:
                    cells.append(
                        Text("[x]" if checked else "[ ]", style=th.ok if checked else th.dim)
                    )
                else:
                    cells.append(Text(""))
            cells += [label, hint]
            grid.add_row(*cells)

        if not vis:
            grid.add_row(*([""] * (3 if not self.multi else 4)))
            grid.add_row(
                *([""] * (1 if not self.multi else 2)), Text(t("ui.no_matches"), style=th.dim), ""
            )

        parts: list[RenderableType] = [grid]
        if self.searching or self.query:
            bar = Text()
            bar.append("/ ", style=th.accent)
            bar.append(self.query, style=th.fg)
            if self.searching:
                bar.append("▏" if not ui.ascii else "_", style=th.accent)
            bar.append(f"   {len(vis)}/{len(self.items)}", style=th.dim)
            parts.append(bar)
        elif len(vis) > height:
            parts.append(Text(f"{self.cursor + 1}/{len(vis)}", style=th.dim, justify="right"))
        return Group(*parts)


def hint_line(ui: UI, *pairs: tuple[str, str]) -> Text:
    """Footer like ``j/k move  Enter select`` built from (keys, i18n-key) pairs."""
    line = Text()
    for i, (keys, label_key) in enumerate(pairs):
        if i:
            line.append("   ")
        line.append(keys, style=f"bold {ui.theme.accent}")
        line.append(f" {t(label_key)}", style=ui.theme.dim)
    return line


def panel(
    ui: UI, body: RenderableType, title: str = "", width: int | None = None, subtitle: str = ""
) -> Panel:
    return Panel(
        body,
        title=Text(f" {title} ", style=f"bold {ui.theme.brand}") if title else None,
        subtitle=Text(f" {subtitle} ", style=ui.theme.dim) if subtitle else None,
        border_style=ui.theme.border,
        box=ui.box,
        padding=(0, 1),
        width=width,
    )


def run_screen(
    ui: UI,
    render: Callable[[], RenderableType],
    on_key: Callable[[str], Any],
    *,
    fullscreen: bool = True,
    timeout: float | None = None,
    on_tick: Callable[[], Any] | None = None,
) -> Any:
    """Render/handle loop. ``on_key`` returns CONTINUE to keep going, else the result.

    With ``timeout`` the screen refreshes even without input (``on_tick`` may also end it).
    """
    with (
        KeyReader() as kr,
        Live(
            render(),
            console=ui.console,
            screen=fullscreen,
            auto_refresh=False,
            transient=not fullscreen,
        ) as live,
    ):
        while True:
            live.update(render(), refresh=True)
            key = kr.read(timeout)
            if key is None:
                if on_tick is not None:
                    res = on_tick()
                    if res is not CONTINUE:
                        return res
                continue
            if key == "":
                continue
            res = on_key(key)
            if res is not CONTINUE:
                return res


def choose(
    ui: UI,
    items: list[Item],
    title: str,
    *,
    header: RenderableType | None = None,
    multi: bool = False,
    fullscreen: bool = True,
    width: int | None = None,
    initial: int = 0,
) -> Any:
    """Show a list and return the chosen Item (or list of Items when ``multi``). None = cancelled."""
    lv = ListView(items, multi=multi)
    lv.cursor = max(0, min(initial, len(items) - 1))

    def render() -> RenderableType:
        used = 6 + (4 if header is not None else 0)
        rows = max(ui.height - used, 3) if fullscreen else min(len(items), max(ui.height - used, 3))
        body: list[RenderableType] = []
        if header is not None:
            body.append(header)
            body.append(Text(""))
        body.append(lv.render(ui, rows))
        body.append(Text(""))
        keys = [
            ("j/k", "hint.move"),
            ("Enter", "hint.select"),
            ("/", "hint.search"),
            ("Esc", "hint.back"),
        ]
        if multi:
            keys.insert(2, ("Space", "hint.toggle"))
        body.append(hint_line(ui, *keys))
        return panel(ui, Group(*body), title, width=width)

    def on_key(key: str) -> Any:
        res = lv.handle(key)
        if res == "cancel":
            return None
        if res == "enter":
            if multi:
                return lv.selected_items() or [lv.current()]
            return lv.current()
        return CONTINUE

    return run_screen(ui, render, on_key, fullscreen=fullscreen)


def prompt_text(
    ui: UI,
    title: str,
    *,
    initial: str = "",
    hint: str = "",
    validator: Callable[[str], str | None] | None = None,
    fullscreen: bool = True,
) -> str | None:
    """Single-line input. Returns the text, or None when cancelled with Esc."""
    state = {"value": initial, "error": ""}

    def render() -> RenderableType:
        line = Text()
        line.append(f"{ui.g.cursor} ", style=ui.theme.accent)
        line.append(state["value"], style=ui.theme.fg)
        line.append("▏" if not ui.ascii else "_", style=ui.theme.accent)
        body: list[RenderableType] = []
        if hint:
            body += [Text(hint, style=ui.theme.dim), Text("")]
        body.append(line)
        if state["error"]:
            body.append(Text(state["error"], style=ui.theme.err))
        body += [Text(""), hint_line(ui, ("Enter", "hint.confirm"), ("Esc", "hint.cancel"))]
        return panel(ui, Group(*body), title, width=min(ui.width, 72))

    def on_key(key: str) -> Any:
        if key == "esc":
            return None
        if key == "enter":
            if validator:
                err = validator(state["value"])
                if err:
                    state["error"] = err
                    return CONTINUE
            return state["value"]
        if key == "backspace":
            state["value"] = state["value"][:-1]
        elif key == "ctrl-u":
            state["value"] = ""
        elif key == "space":
            state["value"] += " "
        elif len(key) == 1 and key.isprintable():
            state["value"] += key
        state["error"] = ""
        return CONTINUE

    return run_screen(ui, render, on_key, fullscreen=fullscreen)


def wait_key(ui: UI, message: str | None = None) -> None:
    """Print ``message`` (dim) and wait for any key."""
    ui.console.print(Text(message or t("ui.press_any_key"), style=ui.theme.dim))
    with KeyReader() as kr:
        kr.read()


def format_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} GB"  # pragma: no cover
