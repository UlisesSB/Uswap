"""Quick pop-up mode: `uswap <file>` (used by the OS context menus)."""

from __future__ import annotations

import time
from pathlib import Path

from rich.console import Group, RenderableType
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

from uswap.core import converter, detector
from uswap.tui.banner import render_banner
from uswap.tui.theme import UI
from uswap.tui.widgets import (
    CONTINUE,
    Item,
    ListView,
    format_size,
    hint_line,
    panel,
    run_screen,
    wait_key,
)
from uswap.utils.config import Config
from uswap.utils.i18n import t

WIDTH = 64


def _file_card(ui: UI, info: detector.FileInfo) -> RenderableType:
    th = ui.theme
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style=th.dim)
    grid.add_column(style=th.fg, overflow="ellipsis", no_wrap=True)
    grid.add_row(t("popup.file"), Text(info.path.name, style=f"bold {th.fg}"))
    grid.add_row(t("popup.type"), f"{info.label} ({info.mime})")
    grid.add_row(t("popup.size"), format_size(info.size))
    if info.mismatch:
        grid.add_row(
            "", Text(t("popup.mismatch", declared=info.declared_ext, real=info.ext), style=th.warn)
        )
    return grid


def _pick_target(ui: UI, info: detector.FileInfo) -> str | None:
    items = [
        Item(f"{i + 1}  {tgt.upper()}", tgt, hint=_target_hint(tgt))
        for i, tgt in enumerate(info.targets[:9])
    ] + [Item(f"   {tgt.upper()}", tgt, hint=_target_hint(tgt)) for tgt in info.targets[9:]]
    lv = ListView(items)

    def render() -> RenderableType:
        rows = min(len(items), max(ui.height - 14, 3))
        body = Group(
            render_banner(ui, compact=True),
            Text(""),
            _file_card(ui, info),
            Text(""),
            Text(t("popup.convert_to"), style=f"bold {ui.theme.accent}"),
            lv.render(ui, rows),
            Text(""),
            hint_line(
                ui,
                ("1-9", "hint.quick"),
                ("j/k", "hint.move"),
                ("Enter", "hint.convert"),
                ("Esc", "hint.quit"),
            ),
        )
        return panel(ui, body, "USwap", width=min(ui.width, WIDTH))

    def on_key(key: str):
        if not lv.searching and len(key) == 1 and key.isdigit() and key != "0":
            idx = int(key) - 1
            if idx < len(items):
                return items[idx].value
            return CONTINUE
        res = lv.handle(key)
        if res == "cancel":
            return None
        if res == "enter":
            return lv.current().value
        return CONTINUE

    return run_screen(ui, render, on_key, fullscreen=False)


def _target_hint(target: str) -> str:
    from uswap.core.formats import label_of

    return label_of(target)


def run(ui: UI, config: Config, path: Path) -> int:
    """Run the pop-up for one file. Returns a process exit code."""
    th, g = ui.theme, ui.g
    console = ui.console
    info = detector.detect(path)

    if not info.supported:
        console.print(Text(f"{g.fail} {path.name}: {t('err.unsupported')}", style=th.err))
        wait_key(ui)
        return 1
    if not info.targets:
        console.print(Text(f"{g.fail} {t('err.no_targets')}", style=th.err))
        wait_key(ui)
        return 1

    target = _pick_target(ui, info)
    if target is None:
        return 130

    progress = Progress(
        SpinnerColumn(style=th.accent),
        TextColumn("{task.description}"),
        BarColumn(bar_width=24, complete_style=th.brand, finished_style=th.ok),
        TaskProgressColumn(),
        console=console,
        transient=True,
    )
    with progress:
        task = progress.add_task(f"{path.name} {g.swap} {target.upper()}", total=100)
        result = converter.convert_file(
            path,
            target,
            config,
            info=info,
            progress=lambda f: progress.update(task, completed=f * 100),
        )

    if result.ok:
        shown = ", ".join(str(o) for o in result.outputs[:3])
        console.print(
            Text(f"{g.ok} {t('popup.done', secs=f'{result.elapsed:.1f}')}", style=f"bold {th.ok}")
        )
        console.print(Text(shown, style=th.dim))
        if config.get("quick_popup.auto_close", True):
            time.sleep(float(config.get("quick_popup.close_delay", 0.8)))
        else:
            wait_key(ui)
        return 0

    console.print(Text(f"{g.fail} {t('popup.failed')}", style=f"bold {th.err}"))
    console.print(Text(converter.format_error(result.error, t), style=th.err))
    wait_key(ui)  # keep the window open so the error can be read
    return 1
