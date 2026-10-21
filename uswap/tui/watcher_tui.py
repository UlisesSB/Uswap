"""Hot-folder watcher screen."""

from __future__ import annotations

import time
from pathlib import Path

from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text

from uswap.core import formats
from uswap.tui import browser
from uswap.tui.theme import UI
from uswap.tui.widgets import (
    CONTINUE,
    Item,
    choose,
    hint_line,
    panel,
    prompt_text,
    run_screen,
)
from uswap.utils.config import Config
from uswap.utils.i18n import t
from uswap.watcher.monitor import FolderMonitor, Rule, rules_from_config


def pick_rule(ui: UI) -> Rule | None:
    """Interactive creation of one rule (used by settings and the watcher)."""
    cats = [Item(c, c, hint=t("watch.category")) for c in formats.CATEGORIES]
    cats.append(Item(t("watch.custom_ext"), "__ext__"))
    first = choose(ui, cats, t("watch.rule_match"))
    if first is None:
        return None
    if first.value == "__ext__":
        ext = prompt_text(
            ui,
            t("watch.rule_ext"),
            hint=t("watch.rule_ext_hint"),
            validator=lambda v: (
                None if formats.normalize_ext(v) in formats.FORMATS else t("watch.unknown_ext")
            ),
        )
        if not ext:
            return None
        match = formats.normalize_ext(ext)
        targets = formats.all_targets(match)
    else:
        match = first.value
        targets = formats.TARGETS[match]
    if not targets:
        return None
    second = choose(
        ui, [Item(x.upper(), x, hint=formats.label_of(x)) for x in targets], t("watch.rule_target")
    )
    if second is None:
        return None
    return Rule(match, second.value)


def _render(ui: UI, mon: FolderMonitor) -> RenderableType:
    th, g = ui.theme, ui.g
    state = Text()
    state.append(f"{g.dot} ", style=th.warn if mon.paused else th.ok)
    state.append(t("watch.paused") if mon.paused else t("watch.running"), style=f"bold {th.fg}")
    state.append(f"   {mon.path}", style=th.dim)

    rules = Table.grid(padding=(0, 2))
    if mon.rules:
        for r in mon.rules:
            rules.add_row(
                Text(r.match, style=th.accent),
                Text(g.swap, style=th.dim),
                Text(r.target, style=th.fg),
            )
    else:
        rules.add_row(Text(t("watch.no_rules"), style=th.warn))

    counts = Text()
    counts.append(f"{g.ok} {mon.counts['ok']}  ", style=th.ok)
    counts.append(f"{g.fail} {mon.counts['error']}  ", style=th.err)
    counts.append(f"{g.dot} {mon.counts['skipped']}", style=th.dim)

    log = Table.grid(padding=(0, 2), expand=True)
    log.add_column(width=8, style=th.dim)
    log.add_column(width=1)
    log.add_column(ratio=1, no_wrap=True, overflow="ellipsis")
    log.add_column(no_wrap=True, justify="right", style=th.dim)
    rows = max(ui.height - 16 - len(mon.rules), 3)
    for ev in list(mon.events)[:rows]:
        mark = {"ok": Text(g.ok, style=th.ok), "error": Text(g.fail, style=th.err)}.get(
            ev.status, Text(g.dot, style=th.dim)
        )
        log.add_row(
            time.strftime("%H:%M:%S", time.localtime(ev.when)), mark, ev.src.name, ev.message
        )
    if not mon.events:
        log.add_row("", "", Text(t("watch.waiting"), style=th.dim), "")

    body = Group(
        state,
        Text(""),
        Text(t("watch.rules"), style=f"bold {th.accent}"),
        rules,
        Text(""),
        counts,
        Text(""),
        log,
        Text(""),
        hint_line(ui, ("p", "hint.pause"), ("q", "hint.stop")),
    )
    return panel(ui, body, t("watch.title"))


def run(ui: UI, config: Config, path: Path | None = None, rules: list[Rule] | None = None) -> int:
    console = ui.console
    if path is None:
        picked = browser.browse(ui, dir_mode=True)
        if not picked:
            return 130
        path = picked[0]
    path = Path(path)
    if not path.is_dir():
        console.print(Text(t("err.not_a_dir", path=str(path)), style=ui.theme.err))
        return 2

    rules = rules if rules is not None else rules_from_config(config)
    if not rules:
        rule = pick_rule(ui)
        if rule is None:
            return 130
        rules = [rule]
        config.set("watcher.rules", [{"match": rule.match, "target": rule.target}])
        config.save()

    mon = FolderMonitor(path, config, rules, recursive=bool(config.get("watcher.recursive", False)))
    mon.start()

    def on_key(key: str):
        if key in ("q", "esc"):
            return True
        if key == "p":
            mon.toggle_pause()
        return CONTINUE

    try:
        run_screen(ui, lambda: _render(ui, mon), on_key, timeout=0.5, on_tick=lambda: CONTINUE)
    except KeyboardInterrupt:
        pass
    finally:
        mon.stop()
    return 0
