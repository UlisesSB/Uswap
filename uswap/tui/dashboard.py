"""Main menu shown by `uswap` without arguments."""

from __future__ import annotations

from pathlib import Path

from rich.console import Group
from rich.text import Text

from uswap.tui import batch_tui, browser, config_tui, quick_popup, watcher_tui
from uswap.tui.banner import render_banner
from uswap.tui.theme import UI
from uswap.tui.widgets import CONTINUE, Item, ListView, hint_line, panel, run_screen
from uswap.utils import system
from uswap.utils.config import Config
from uswap.utils.i18n import t


def _menu() -> list[Item]:
    return [
        Item(t("menu.convert"), "convert", hint=t("menu.convert_hint")),
        Item(t("menu.batch"), "batch", hint=t("menu.batch_hint")),
        Item(t("menu.watch"), "watch", hint=t("menu.watch_hint")),
        Item(t("menu.config"), "config", hint=t("menu.config_hint")),
        Item(t("menu.doctor"), "doctor", hint=t("menu.doctor_hint")),
        Item(t("menu.quit"), "quit", hint="q"),
    ]


def run(ui: UI, config: Config) -> int:
    lv = ListView(_menu(), searchable=False)

    def render():
        th = ui.theme
        missing = [d.name for d in system.check_all() if not d.available]
        body = [render_banner(ui), Text(""), lv.render(ui, 8), Text("")]
        if missing:
            body.append(
                Text(f"{ui.g.fail} {t('menu.missing', names=', '.join(missing))}", style=th.warn)
            )
            body.append(Text(""))
        body.append(
            hint_line(ui, ("j/k", "hint.move"), ("Enter", "hint.select"), ("q", "hint.quit"))
        )
        return panel(ui, Group(*body), width=min(ui.width, 84))

    def on_key(key: str):
        if key == "q" and not lv.searching:
            return "quit"
        res = lv.handle(key)
        if res == "cancel":
            return "quit"
        if res == "enter":
            return lv.current().value
        return CONTINUE

    while True:
        action = run_screen(ui, render, on_key)
        if action in (None, "quit"):
            return 0
        if action == "convert":
            picked = browser.browse(ui)
            if picked:
                quick_popup.run(ui, config, Path(picked[0]))
        elif action == "batch":
            batch_tui.run(ui, config, wait=True)
        elif action == "watch":
            watcher_tui.run(ui, config)
        elif action == "config":
            config_tui.run(ui, config)
            lv.set_items(_menu(), keep_cursor=True)
        elif action == "doctor":
            system.clear_cache()
            config_tui.show_doctor(ui)
