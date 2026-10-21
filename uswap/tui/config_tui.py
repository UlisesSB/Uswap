"""Settings panel."""

from __future__ import annotations

from rich.console import Group
from rich.text import Text

from uswap.tui import doctor
from uswap.tui.theme import UI
from uswap.tui.watcher_tui import pick_rule
from uswap.tui.widgets import (
    CONTINUE,
    Item,
    choose,
    hint_line,
    panel,
    prompt_text,
    run_screen,
    wait_key,
)
from uswap.utils import i18n
from uswap.utils.config import CHOICES, Config
from uswap.utils.i18n import t

LANG_NAMES = {"auto": "auto", "en": "English", "es": "Español"}


def _display(key: str, value) -> str:
    if key == "language":
        return LANG_NAMES.get(str(value), str(value))
    if key in CHOICES and isinstance(value, str):
        label = t(f"opt.{key}.{value}")
        return value if label == f"opt.{key}.{value}" else label
    if value in ("", None):
        return "-"
    return str(value)


def _choice(ui: UI, config: Config, key: str, title: str) -> None:
    opts = CHOICES[key]
    current = config.get(key)
    items = [Item(_display(key, o), o, hint=t("cfg.current") if o == current else "") for o in opts]
    picked = choose(ui, items, title, initial=opts.index(current) if current in opts else 0)
    if picked is not None:
        config.set(key, picked.value)
        config.save()
        if key == "language":
            i18n.set_language(picked.value)
        if key in ("theme", "glyphs"):
            ui.reload(config)


def _int_field(ui: UI, config: Config, key: str, title: str, lo: int, hi: int) -> None:
    def valid(v: str) -> str | None:
        try:
            return None if lo <= int(v) <= hi else t("cfg.range", lo=lo, hi=hi)
        except ValueError:
            return t("cfg.range", lo=lo, hi=hi)

    val = prompt_text(
        ui, title, initial=str(config.get(key)), validator=valid, hint=t("cfg.range", lo=lo, hi=hi)
    )
    if val is not None:
        config.set(key, int(val))
        config.save()


def _text_field(ui: UI, config: Config, key: str, title: str, hint: str = "") -> None:
    val = prompt_text(ui, title, initial=str(config.get(key, "")), hint=hint)
    if val is not None:
        config.set(key, val.strip())
        config.save()


def _rules_menu(ui: UI, config: Config) -> None:
    while True:
        rules = list(config.get("watcher.rules", []) or [])
        items = [Item(t("cfg.rules_add"), "__add__", style=f"bold {ui.theme.ok}")]
        items += [
            Item(f"{r['match']}  {ui.g.swap}  {r['target']}", i, hint=t("cfg.rules_delete_hint"))
            for i, r in enumerate(rules)
        ]
        picked = choose(ui, items, t("cfg.rules_title"))
        if picked is None:
            return
        if picked.value == "__add__":
            rule = pick_rule(ui)
            if rule:
                rules.append({"match": rule.match, "target": rule.target})
        else:
            rules.pop(picked.value)  # Enter on an existing rule deletes it
        config.set("watcher.rules", rules)
        config.save()


def _items(config: Config) -> list[Item]:
    def it(label_key: str, key: str, action: str) -> Item:
        return Item(t(label_key), action, hint=_display(key, config.get(key)))

    return [
        it("cfg.language", "language", "language"),
        it("cfg.theme", "theme", "theme"),
        it("cfg.glyphs", "glyphs", "glyphs"),
        it("cfg.out_mode", "output.mode", "output.mode"),
        it("cfg.out_dir", "output.custom_dir", "output.custom_dir"),
        it("cfg.naming", "output.naming", "output.naming"),
        it("cfg.suffix", "output.suffix", "output.suffix"),
        it("cfg.quality", "quality.image", "quality.image"),
        it("cfg.workers", "batch.workers", "batch.workers"),
        Item(t("cfg.rules"), "rules", hint=str(len(config.get("watcher.rules", []) or []))),
        Item(t("cfg.doctor"), "doctor"),
    ]


def run(ui: UI, config: Config) -> int:
    from uswap.tui.widgets import ListView

    lv = ListView(_items(config), searchable=False)

    def render():
        body = Group(
            lv.render(ui, max(ui.height - 8, 3)),
            Text(""),
            hint_line(ui, ("j/k", "hint.move"), ("Enter", "hint.edit"), ("Esc", "hint.back")),
            Text(f"{config.path}", style=ui.theme.dim),
        )
        return panel(ui, body, t("cfg.title"))

    def on_key(key: str):
        res = lv.handle(key)
        if res == "cancel":
            return "quit"
        if res == "enter":
            return lv.current().value
        return CONTINUE

    while True:
        action = run_screen(ui, render, on_key)
        if action == "quit":
            return 0
        if action in ("language", "theme", "glyphs", "output.mode", "output.naming"):
            _choice(
                ui,
                config,
                action,
                t(
                    "cfg."
                    + {"output.mode": "out_mode", "output.naming": "naming"}.get(action, action)
                ),
            )
        elif action == "output.custom_dir":
            _text_field(ui, config, action, t("cfg.out_dir"), t("cfg.out_dir_hint"))
        elif action == "output.suffix":
            _text_field(ui, config, action, t("cfg.suffix"))
        elif action == "quality.image":
            _int_field(ui, config, action, t("cfg.quality"), 1, 100)
        elif action == "batch.workers":
            _int_field(ui, config, action, t("cfg.workers"), 1, 32)
        elif action == "rules":
            _rules_menu(ui, config)
        elif action == "doctor":
            show_doctor(ui)
        lv.set_items(_items(config), keep_cursor=True)


def show_doctor(ui: UI) -> None:
    ui.console.print(
        panel(
            ui,
            Group(
                doctor.render_doctor(ui),
                *[Text(h, style=ui.theme.dim) for h in doctor.hints_for_missing()],
            ),
            t("doctor.title"),
        )
    )
    wait_key(ui)
