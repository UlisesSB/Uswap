"""Batch conversion: multi-select, pick a target, convert in parallel."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.console import Group
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from uswap.core import converter, detector
from uswap.core.converter import ConversionResult
from uswap.core.formats import label_of
from uswap.tui import browser
from uswap.tui.theme import UI
from uswap.tui.widgets import Item, choose, wait_key
from uswap.utils.config import Config
from uswap.utils.i18n import t


def run_batch(
    ui: UI, config: Config, infos: list[detector.FileInfo], target: str, workers: int | None = None
) -> list[ConversionResult]:
    """Convert ``infos`` to ``target`` in a thread pool, showing live progress bars."""
    th, g, console = ui.theme, ui.g, ui.console
    workers = max(1, int(workers or config.get("batch.workers", 4)))
    cancel = threading.Event()
    results: list[ConversionResult] = []

    progress = Progress(
        SpinnerColumn(style=th.accent),
        TextColumn("{task.description}", justify="left"),
        BarColumn(bar_width=None, complete_style=th.brand, finished_style=th.ok),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        expand=True,
    )
    overall = progress.add_task(t("batch.overall"), total=len(infos))

    def work(info: detector.FileInfo) -> ConversionResult:
        tid = progress.add_task(info.path.name, total=100)
        try:
            return converter.convert_file(
                info.path,
                target,
                config,
                info=info,
                cancel=cancel,
                progress=lambda f: progress.update(tid, completed=f * 100),
            )
        finally:
            progress.remove_task(tid)

    with progress, ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, info): info for info in infos}
        try:
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)
                progress.advance(overall)
                if res.ok:
                    progress.console.print(Text(f"{g.ok} {res.src.name}", style=th.ok))
                else:
                    msg = converter.format_error(res.error, t).splitlines()[0]
                    progress.console.print(Text(f"{g.fail} {res.src.name}: {msg}", style=th.err))
        except KeyboardInterrupt:
            cancel.set()
            pool.shutdown(wait=True, cancel_futures=True)
            progress.console.print(Text(t("batch.cancelled"), style=th.warn))
    return results


def summary(ui: UI, results: list[ConversionResult]):
    th, g = ui.theme, ui.g
    ok = [r for r in results if r.ok and not r.skipped]
    skipped = [r for r in results if r.skipped]
    failed = [r for r in results if not r.ok]
    table = Table.grid(padding=(0, 2))
    table.add_row(
        Text(f"{g.ok} {t('batch.converted')}", style=th.ok),
        Text(str(len(ok)), style=f"bold {th.ok}"),
    )
    if skipped:
        table.add_row(
            Text(f"{g.dot} {t('batch.skipped')}", style=th.dim),
            Text(str(len(skipped)), style=th.dim),
        )
    if failed:
        table.add_row(
            Text(f"{g.fail} {t('batch.failed')}", style=th.err),
            Text(str(len(failed)), style=f"bold {th.err}"),
        )
    return Group(Text(""), table)


def run(
    ui: UI,
    config: Config,
    files: list[Path] | None = None,
    target: str | None = None,
    *,
    wait: bool = False,
    workers: int | None = None,
) -> int:
    """Interactive batch flow. ``files=None`` opens the multi-select browser."""
    th, console = ui.theme, ui.console
    if files is None:
        chosen = browser.browse(ui, multi=True)
        if not chosen:
            return 130
        files = chosen

    infos = [detector.detect(p) for p in files]
    good = [i for i in infos if i.supported]
    bad = [i for i in infos if not i.supported]
    for info in bad:
        console.print(Text(f"{ui.g.fail} {info.path.name}: {t('err.unsupported')}", style=th.warn))
    if not good:
        console.print(Text(t("err.nothing_to_convert"), style=th.err))
        if wait:
            wait_key(ui)
        return 1

    if target is None:
        options = detector.common_targets(good)
        if not options:
            console.print(Text(t("err.no_common_targets"), style=th.err))
            if wait:
                wait_key(ui)
            return 1
        header = Text(t("batch.n_files", n=len(good)), style=th.dim)
        picked = choose(
            ui,
            [Item(x.upper(), x, hint=label_of(x)) for x in options],
            t("batch.pick_target"),
            header=header,
        )
        if picked is None:
            return 130
        target = picked.value

    results = run_batch(ui, config, good, target, workers=workers)
    console.print(summary(ui, results))
    if wait:
        wait_key(ui)
    return 0 if all(r.ok for r in results) else 1
