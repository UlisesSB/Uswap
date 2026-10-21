# Architecture

```text
uswap/
├── cli.py                 argument parsing, mode dispatch, headless conversion
├── core/
│   ├── formats.py         format registry, aliases, targets per category, engine routing
│   ├── detector.py        magic-byte detection -> FileInfo, targets_for()
│   ├── converter.py       output naming + engine dispatch -> ConversionResult
│   ├── engine_image.py    Pillow
│   ├── engine_media.py    FFmpeg (subprocess, -progress parsing)
│   ├── engine_doc.py      Pandoc + Poppler
│   └── errors.py
├── tui/
│   ├── keys.py            raw keyboard (termios / msvcrt) -> key names
│   ├── theme.py           themes, glyph sets, UI context
│   ├── widgets.py         ListView, choose(), prompt_text(), run_screen()
│   ├── banner.py          isotype + banner
│   ├── browser.py         file browser (single / multi / directory)
│   ├── quick_popup.py     single-file pop-up
│   ├── batch_tui.py       parallel batch with rich.progress
│   ├── watcher_tui.py     watcher screen + rule picker
│   ├── config_tui.py      settings
│   ├── dashboard.py       main menu
│   └── doctor.py          dependency table
├── utils/
│   ├── config.py          JSON config (defaults merge, dotted keys)
│   ├── i18n.py            EN/ES strings
│   └── system.py          dependency inspector
├── watcher/monitor.py     watchdog + worker thread, rules
└── locales/{en,es}.json
```

## Data flow

```text
path --detector.detect--> FileInfo(ext, category, targets)
                              |
          (user or --to picks target)
                              v
converter.convert_file --resolve_output--> dst path (config rules)
        |
        +-- engine_for(ext, target) --> image | media | pandoc | poppler
        v
ConversionResult(ok, outputs, error)   # never raises
```

## Key decisions

* **Engines never reach the UI with exceptions.** `convert_file` catches everything and returns a `ConversionResult`; errors are machine-readable strings (`missing:ffmpeg`, `no_route:...`) translated by `converter.format_error`.
* **Targets are filtered by installed tools.** `detector.targets_for` asks `utils.system` which engines exist, so the UI never offers an impossible conversion.
* **No heavy TUI framework.** `rich` renders; `keys.py` reads keys. Screens are `render()` + `on_key()` pairs driven by `widgets.run_screen`, which keeps every screen testable and small. Only one `rich.live.Live` can be active at a time, so screens never nest: they run in sequence.
* **FFmpeg through `subprocess`**, not `ffmpeg-python`: one dependency less, and `-progress pipe:1` gives progress for the bar. stderr is merged into stdout and split into progress keys vs. error text to avoid pipe deadlocks.
* **Cancellation** via a shared `threading.Event` checked by the media/document engines.
* **Watcher loop prevention**: outputs are recorded in a set and checked both when queued and when processed (events can arrive before the result is recorded).
* **Locales live inside the package** (`uswap/locales`) so they ship in the wheel.

## Adding a format

1. Register it in `core/formats.py` (`_FORMATS`, `TARGETS`, `ALIASES` if needed).
2. Add its magic bytes to `detector.sniff`.
3. Implement the conversion in the engine (e.g. an entry in `engine_media.ARGS`).
4. Add tests (`tests/test_detector.py`, `tests/test_converter.py`) and mention it in the README table.

## Adding a language

Copy `uswap/locales/en.json` to `xx.json`, translate the values (keep `{placeholders}`), add `"xx"` to `i18n.SUPPORTED` and to `config.CHOICES["language"]`. `tests/test_i18n.py` verifies key and placeholder parity.
