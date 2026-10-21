"""Hot-folder daemon: converts files as they appear in a directory."""

from __future__ import annotations

import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from uswap.core import converter, detector, formats
from uswap.utils.config import Config

IGNORED_SUFFIXES = {".part", ".crdownload", ".tmp", ".temp", ".partial", ".download", ".swp"}


@dataclass
class Rule:
    """``match`` is an extension (``png``), a category (``image``) or ``*``."""

    match: str
    target: str

    def applies_to(self, info: detector.FileInfo) -> bool:
        m = self.match.lower().lstrip(".")
        return m == "*" or m == info.category or formats.normalize_ext(m) == info.ext

    @classmethod
    def parse(cls, text: str) -> Rule:
        """Parse ``png:webp`` / ``image:webp``."""
        match, sep, target = text.partition(":")
        if not sep or not match.strip() or not target.strip():
            raise ValueError(f"invalid rule {text!r} (expected MATCH:TARGET, e.g. png:webp)")
        return cls(match.strip().lower(), formats.normalize_ext(target.strip()))


@dataclass
class WatchEvent:
    when: float
    src: Path
    status: str  # ok | error | skipped
    message: str = ""
    outputs: list[Path] = field(default_factory=list)


def rules_from_config(config: Config) -> list[Rule]:
    rules = []
    for raw in config.get("watcher.rules", []) or []:
        try:
            rules.append(Rule(str(raw["match"]).lower(), formats.normalize_ext(str(raw["target"]))))
        except (KeyError, TypeError):
            continue
    return rules


class _Handler(FileSystemEventHandler):
    def __init__(self, monitor: FolderMonitor):
        self.monitor = monitor

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.monitor.enqueue(Path(str(event.src_path)))

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.monitor.enqueue(Path(str(event.dest_path)))


class FolderMonitor:
    def __init__(self, path: Path, config: Config, rules: list[Rule], recursive: bool = False):
        self.path = Path(path).resolve()
        self.config = config
        self.rules = rules
        self.recursive = recursive
        self.events: deque[WatchEvent] = deque(maxlen=200)
        self.counts = {"ok": 0, "error": 0, "skipped": 0}
        self.paused = False
        self._queue: queue.Queue[Path | None] = queue.Queue()
        self._produced: set[Path] = set()  # files we created: never re-convert them
        self._lock = threading.Lock()
        self._observer = Observer()
        self._worker = threading.Thread(target=self._run, name="uswap-watch", daemon=True)
        self._stop = threading.Event()

    # -- lifecycle -------------------------------------------------------
    def start(self) -> None:
        self._observer.schedule(_Handler(self), str(self.path), recursive=self.recursive)
        self._observer.start()
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        self._queue.put(None)
        self._observer.stop()
        self._observer.join(timeout=3)
        self._worker.join(timeout=3)

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused

    # -- internals -------------------------------------------------------
    def enqueue(self, path: Path) -> None:
        if self.paused:
            return
        if path.name.startswith(".") or path.suffix.lower() in IGNORED_SUFFIXES:
            return
        with self._lock:
            if path.resolve() in self._produced:
                return
        self._queue.put(path)

    def _wait_stable(self, path: Path, timeout: float = 60.0) -> bool:
        """Wait until the file stops growing (e.g. a download in progress)."""
        deadline = time.monotonic() + timeout
        last = -1
        while time.monotonic() < deadline and not self._stop.is_set():
            try:
                size = path.stat().st_size
            except OSError:
                return False
            if size == last and size > 0:
                try:
                    with path.open("rb"):
                        return True
                except OSError:
                    pass
            last = size
            time.sleep(0.5)
        return False

    def _emit(self, event: WatchEvent) -> None:
        self.events.appendleft(event)
        self.counts[event.status] = self.counts.get(event.status, 0) + 1

    def _run(self) -> None:
        while not self._stop.is_set():
            path = self._queue.get()
            if path is None:
                break
            try:
                self._process(path)
            except Exception as exc:  # the daemon must survive anything
                self._emit(WatchEvent(time.time(), path, "error", f"{type(exc).__name__}: {exc}"))

    def _process(self, path: Path) -> None:
        # Our own outputs raise "created" events too; they may be queued before we
        # registered them, so check again right before processing.
        with self._lock:
            if path.resolve() in self._produced:
                return
        if not self._wait_stable(path):
            return
        info = detector.detect(path)
        if not info.supported:
            self._emit(WatchEvent(time.time(), path, "skipped", "unsupported"))
            return
        rule = next((r for r in self.rules if r.applies_to(info) and r.target != info.ext), None)
        if rule is None:
            self._emit(WatchEvent(time.time(), path, "skipped", "no rule"))
            return
        if rule.target not in info.targets:
            self._emit(
                WatchEvent(
                    time.time(), path, "error", f"cannot convert {info.ext} -> {rule.target}"
                )
            )
            return
        result = converter.convert_file(path, rule.target, self.config, info=info)
        if result.ok:
            with self._lock:
                for out in result.outputs:
                    self._produced.add(out.resolve())
            self._emit(
                WatchEvent(time.time(), path, "ok", f"{info.ext} -> {rule.target}", result.outputs)
            )
        else:
            self._emit(WatchEvent(time.time(), path, "error", result.error))
