"""Interactive file browser (single pick, multi-select, or directory pick)."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path

from rich.console import Group, RenderableType
from rich.text import Text

from uswap.core import formats
from uswap.tui.theme import UI
from uswap.tui.widgets import (
    CONTINUE,
    Item,
    ListView,
    hint_line,
    panel,
    run_screen,
)
from uswap.utils.i18n import t

SELECT_HERE = "__select_here__"


def _is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if os.name == "nt":
        try:
            import stat

            return bool(path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)  # type: ignore[attr-defined]
        except (OSError, AttributeError):
            return False
    return False


def _supported_ext(path: Path) -> bool:
    return formats.normalize_ext(path.suffix) in formats.FORMATS


class FileBrowser:
    """State machine behind :func:`browse`."""

    def __init__(self, ui: UI, start: Path, *, multi: bool, dir_mode: bool):
        self.ui = ui
        self.cwd = start.resolve()
        self.multi = multi
        self.dir_mode = dir_mode
        self.show_hidden = False
        self.picked: set[Path] = set()  # persists across directories
        self.error = ""
        self.globbing = False  # typing a wildcard pattern
        self.glob = "*"
        self.view = ListView([], multi=multi)
        self._load()

    # -- data ------------------------------------------------------------
    def _load(self) -> None:
        g = self.ui.g
        items: list[Item] = []
        if self.dir_mode:
            items.append(
                Item(
                    t("browser.select_here"),
                    SELECT_HERE,
                    style=f"bold {self.ui.theme.ok}",
                    selectable=False,
                )
            )
        if self.cwd.parent != self.cwd:
            items.append(Item("..", self.cwd.parent, style=self.ui.theme.dim, selectable=False))
        try:
            entries = [p for p in self.cwd.iterdir() if self.show_hidden or not _is_hidden(p)]
            self.error = ""
        except OSError as exc:
            entries, self.error = [], exc.strerror or str(exc)
        dirs = sorted((p for p in entries if _safe_is_dir(p)), key=lambda p: p.name.lower())
        files = sorted((p for p in entries if not _safe_is_dir(p)), key=lambda p: p.name.lower())
        for d in dirs:
            items.append(Item(f"{g.dir} {d.name}", d, style=self.ui.theme.accent, selectable=False))
        if not self.dir_mode:
            for f in files:
                ok = _supported_ext(f)
                items.append(
                    Item(
                        f.name,
                        f,
                        hint=_hint(f),
                        enabled=True,
                        style="" if ok else self.ui.theme.dim,
                    )
                )
        self.view.set_items(items)
        self.view.selected = {
            i
            for i, it in enumerate(items)
            if isinstance(it.value, Path) and it.value in self.picked
        }

    def cd(self, path: Path) -> None:
        self.cwd = path.resolve()
        self.view.query = ""
        self._load()

    def _sync_picked(self) -> None:
        here = {
            it.value
            for it in self.view.items
            if isinstance(it.value, Path) and not _safe_is_dir(it.value)
        }
        chosen = {self.view.items[i].value for i in self.view.selected}
        self.picked = (self.picked - here) | chosen

    def _toggle_files(self, predicate) -> int:
        idxs = {
            i
            for i, it in enumerate(self.view.items)
            if isinstance(it.value, Path) and not _safe_is_dir(it.value) and predicate(it.value)
        }
        if not idxs:
            return 0
        if idxs <= self.view.selected:
            self.view.selected -= idxs
        else:
            self.view.selected |= idxs
        self._sync_picked()
        return len(idxs)

    # -- render ----------------------------------------------------------
    def render(self) -> RenderableType:
        ui = self.ui
        th = ui.theme
        path = Text(str(self.cwd), style=f"bold {th.fg}", overflow="ellipsis", no_wrap=True)
        rows = max(ui.height - 8, 3)
        body: list[RenderableType] = [
            path,
            Text(
                "─" * max(min(ui.width - 6, 100), 10) if not ui.ascii else "-" * 20, style=th.border
            ),
        ]
        body.append(self.view.render(ui, rows))
        if self.error:
            body.append(Text(self.error, style=th.err))
        if self.globbing:
            bar = Text()
            bar.append(f"{t('browser.glob_title')}: ", style=th.accent)
            bar.append(self.glob, style=th.fg)
            bar.append("▏" if not ui.ascii else "_", style=th.accent)
            body.append(bar)
        body.append(Text(""))
        status = Text()
        if self.multi:
            status.append(
                t("browser.selected", n=len(self.picked)), style=th.ok if self.picked else th.dim
            )
            status.append("   ")
        status.append(t("browser.hidden_on") if self.show_hidden else "", style=th.dim)
        body.append(status)
        keys = [
            ("j/k", "hint.move"),
            ("l/h", "hint.enter_up"),
            ("Enter", "hint.confirm" if self.multi else "hint.open"),
            ("/", "hint.search"),
        ]
        if self.multi:
            keys += [("Space", "hint.toggle"), ("a", "hint.all"), ("*", "hint.glob")]
        keys += [(".", "hint.hidden"), ("Esc", "hint.back")]
        body.append(hint_line(ui, *keys))
        return panel(ui, Group(*body), t("browser.title"))

    # -- input -----------------------------------------------------------
    def _glob_key(self, key: str) -> None:
        v = self.view
        if key == "esc":
            self.globbing = False
        elif key == "enter":
            self.globbing = False
            pattern = self.glob.lower().strip() or "*"
            idxs = {
                i
                for i, it in enumerate(v.items)
                if isinstance(it.value, Path)
                and not _safe_is_dir(it.value)
                and fnmatch.fnmatch(it.value.name.lower(), pattern)
            }
            v.selected |= idxs
            self._sync_picked()
        elif key == "backspace":
            self.glob = self.glob[:-1]
        elif key == "ctrl-u":
            self.glob = ""
        elif len(key) == 1 and key.isprintable():
            self.glob += key

    def on_key(self, key: str):
        v = self.view
        if self.globbing:
            self._glob_key(key)
            return CONTINUE
        if v.searching:
            v.handle(key)
            return CONTINUE
        item = v.current()
        if key in ("right", "l"):
            if item and isinstance(item.value, Path) and _safe_is_dir(item.value):
                self.cd(item.value)
            return CONTINUE
        if key in ("left", "h", "backspace"):
            if self.cwd.parent != self.cwd:
                self.cd(self.cwd.parent)
            return CONTINUE
        if key == ".":
            self.show_hidden = not self.show_hidden
            self._load()
            return CONTINUE
        if key == "~":
            self.cd(Path.home())
            return CONTINUE
        if self.multi and key == "a":
            self._toggle_files(_supported_ext)
            return CONTINUE
        if self.multi and key == "*":
            self.globbing, self.glob = True, "*"
            return CONTINUE
        if key == "space" and self.multi:
            if item and isinstance(item.value, Path) and not _safe_is_dir(item.value):
                v.handle(key)
                self._sync_picked()
            return CONTINUE

        res = v.handle(key)
        if res == "cancel":
            return None
        if res == "enter" and item is not None:
            if item.value == SELECT_HERE:
                return [self.cwd]
            path = item.value
            if self.multi:
                self._sync_picked()
                if self.picked:  # Enter confirms the multi-selection
                    return sorted(self.picked)
            if _safe_is_dir(path):
                self.cd(path)
                return CONTINUE
            return [path]
        return CONTINUE


def _safe_is_dir(p: Path) -> bool:
    try:
        return p.is_dir()
    except OSError:
        return False


def _hint(path: Path) -> str:
    try:
        size = path.stat().st_size
    except OSError:
        return ""
    from uswap.tui.widgets import format_size

    return format_size(size)


def browse(
    ui: UI, start: Path | None = None, *, multi: bool = False, dir_mode: bool = False
) -> list[Path] | None:
    """Open the browser. Returns the chosen paths, or None when cancelled."""
    fb = FileBrowser(ui, start or Path.cwd(), multi=multi, dir_mode=dir_mode)
    return run_screen(ui, fb.render, fb.on_key)
