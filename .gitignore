"""USwap command line entry point."""

from __future__ import annotations

import argparse
import glob
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rich.console import Console
from rich.text import Text

from uswap import __version__
from uswap.core import converter, formats
from uswap.utils import i18n, system
from uswap.utils.config import Config
from uswap.utils.i18n import t

GLOB_CHARS = set("*?[")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="uswap",
        description="USwap - lightweight, keyboard-driven file converter for the terminal.",
        epilog="Run `uswap` with no arguments to open the interactive dashboard.",
    )
    p.add_argument("files", nargs="*", metavar="FILE", help="file(s) to convert (globs allowed)")
    p.add_argument(
        "--to", metavar="FORMAT", help="convert without UI to FORMAT (e.g. png, mp3, docx)"
    )
    p.add_argument("-o", "--output-dir", metavar="DIR", help="write results to DIR (this run only)")
    p.add_argument(
        "-j", "--jobs", type=int, metavar="N", help="parallel workers for batch conversion"
    )
    p.add_argument("--watch", metavar="DIR", help="watch DIR and convert new files automatically")
    p.add_argument(
        "--rule",
        action="append",
        metavar="MATCH:TARGET",
        help="watch rule, e.g. png:webp or image:webp (repeatable)",
    )
    p.add_argument("--config", action="store_true", help="open the settings panel")
    p.add_argument("--doctor", action="store_true", help="check installed dependencies")
    p.add_argument("--formats", action="store_true", help="list supported formats")
    p.add_argument("--lang", choices=["en", "es"], help="UI language for this run")
    p.add_argument("-V", "--version", action="store_true", help="show version and exit")
    return p


def expand_inputs(items: list[str]) -> tuple[list[Path], list[str]]:
    """Expand globs/directories. Returns (files, missing-names)."""
    files: list[Path] = []
    missing: list[str] = []
    for item in items:
        path = Path(item).expanduser()
        if path.is_dir():
            files += sorted(p for p in path.iterdir() if p.is_file() and not p.name.startswith("."))
        elif path.exists():
            files.append(path)
        elif GLOB_CHARS & set(item):
            matches = sorted(glob.glob(str(path)))
            if matches:
                files += [Path(m) for m in matches if Path(m).is_file()]
            else:
                missing.append(item)
        else:
            missing.append(item)
    seen: set[Path] = set()
    unique = []
    for f in files:
        key = f.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique, missing


def _setup_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


def _need_tty(console: Console) -> bool:
    if sys.stdin.isatty() and sys.stdout.isatty():
        return True
    print(t("err.no_tty"), file=sys.stderr)
    return False


def _headless(files: list[Path], target: str, config: Config, console: Console, jobs: int) -> int:
    """Non-interactive conversion (scripts, CI, power users)."""
    target = formats.normalize_ext(target)
    if target not in formats.FORMATS:
        console.print(f"[red]{t('err.unknown_format', fmt=target)}[/red]")
        return 2
    failures = 0

    def one(path: Path) -> converter.ConversionResult:
        return converter.convert_file(path, target, config)

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        for res in pool.map(one, files):
            if res.ok and res.skipped:
                console.print(f"= {res.src.name}: {t('cli.already', fmt=target)}", highlight=False)
            elif res.ok:
                for out in res.outputs:
                    console.print(f"[green]ok[/green] {res.src.name} -> {out}", highlight=False)
            else:
                failures += 1
                msg = converter.format_error(res.error, t).splitlines()[0]
                console.print(f"[red]error[/red] {res.src.name}: {msg}", highlight=False)
    return 1 if failures else 0


def _print_formats(console: Console) -> None:
    for cat in formats.CATEGORIES:
        exts = [f.ext for f in formats.FORMATS.values() if f.category == cat]
        console.print(f"[bold]{cat:<9}[/bold] {' '.join(exts)}", highlight=False)
    console.print()
    for cat, targets in formats.TARGETS.items():
        console.print(f"{cat:<9} -> {' '.join(targets)}", highlight=False)
    console.print(f"{'pdf':<9} -> {' '.join(formats.PDF_TARGETS)}", highlight=False)


def main(argv: list[str] | None = None) -> int:
    _setup_stdio()
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"uswap {__version__}")
        return 0

    config = Config.load()
    i18n.set_language(args.lang or config.get("language", "auto"))
    console = Console()

    if args.output_dir:
        config = config.copy()
        config.set("output.mode", "custom")
        config.set("output.custom_dir", args.output_dir)

    if args.formats:
        _print_formats(console)
        return 0

    from uswap.tui.theme import UI

    ui = UI.from_config(config, console)

    if args.doctor:
        from uswap.tui import doctor

        console.print(doctor.render_doctor(ui))
        for line in doctor.hints_for_missing():
            console.print(Text(line, style=ui.theme.dim))
        return 0 if all(d.available for d in system.check_all() if d.required) else 1

    try:
        if args.config:
            if not _need_tty(console):
                return 2
            from uswap.tui import config_tui

            return config_tui.run(ui, config)

        if args.watch:
            if not _need_tty(console):
                return 2
            from uswap.tui import watcher_tui
            from uswap.watcher.monitor import Rule

            rules = None
            if args.rule:
                try:
                    rules = [Rule.parse(r) for r in args.rule]
                except ValueError as exc:
                    console.print(f"[red]{exc}[/red]")
                    return 2
            return watcher_tui.run(ui, config, Path(args.watch).expanduser(), rules)

        if args.files:
            files, missing = expand_inputs(args.files)
            for name in missing:
                console.print(Text(t("err.not_found", path=name), style=ui.theme.err))
            if not files:
                return 2
            if args.to:
                return _headless(
                    files, args.to, config, console, args.jobs or config.get("batch.workers", 4)
                )
            if not _need_tty(console):
                return 2
            if len(files) == 1:
                from uswap.tui import quick_popup

                return quick_popup.run(ui, config, files[0])
            from uswap.tui import batch_tui

            return batch_tui.run(ui, config, files, workers=args.jobs)

        if not _need_tty(console):
            return 2
        from uswap.tui import dashboard

        return dashboard.run(ui, config)
    except KeyboardInterrupt:
        console.print()
        return 130
    except EOFError:
        return 130


if __name__ == "__main__":
    sys.exit(main())
