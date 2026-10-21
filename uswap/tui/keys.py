"""Cross-platform raw keyboard input.

``KeyReader.read()`` returns normalized key names: ``up``, ``down``, ``left``,
``right``, ``enter``, ``esc``, ``space``, ``tab``, ``backspace``, ``delete``,
``home``, ``end``, ``pgup``, ``pgdn`` or the printable character itself.
"""

from __future__ import annotations

import os
import sys
import time

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import msvcrt

    _WIN_SPECIAL = {
        "H": "up",
        "P": "down",
        "K": "left",
        "M": "right",
        "G": "home",
        "O": "end",
        "I": "pgup",
        "Q": "pgdn",
        "S": "delete",
    }
else:
    import select
    import termios
    import tty

_CSI_FINAL = {"A": "up", "B": "down", "C": "right", "D": "left", "H": "home", "F": "end"}
_CSI_TILDE = {
    "1": "home",
    "7": "home",
    "4": "end",
    "8": "end",
    "5": "pgup",
    "6": "pgdn",
    "3": "delete",
}


def _simple(ch: str) -> str:
    if ch in ("\r", "\n"):
        return "enter"
    if ch == "\t":
        return "tab"
    if ch in ("\x7f", "\x08"):
        return "backspace"
    if ch == " ":
        return "space"
    if ch == "\x03":
        raise KeyboardInterrupt
    if ch == "\x15":
        return "ctrl-u"
    return ch


class KeyReader:
    """Context manager that puts the terminal in cbreak mode (POSIX only)."""

    def __init__(self) -> None:
        self._fd = -1
        self._saved = None

    def __enter__(self) -> KeyReader:
        if not IS_WINDOWS:
            self._fd = sys.stdin.fileno()
            self._saved = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        return self

    def __exit__(self, *exc) -> None:
        if not IS_WINDOWS and self._saved is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved)
            self._saved = None

    # -- POSIX -----------------------------------------------------------
    def _posix_ready(self, timeout: float | None) -> bool:
        return bool(select.select([self._fd], [], [], timeout)[0])

    def _posix_byte(self) -> bytes:
        return os.read(self._fd, 1)

    def _read_posix(self, timeout: float | None) -> str | None:
        if not self._posix_ready(timeout):
            return None
        first = self._posix_byte()
        if not first:
            raise EOFError
        byte = first[0]
        if byte == 0x1B:
            if not self._posix_ready(0.03):
                return "esc"
            nxt = self._posix_byte()
            if nxt not in (b"[", b"O"):
                return "esc"
            seq = ""
            while self._posix_ready(0.03):
                c = self._posix_byte().decode("latin-1")
                seq += c
                if 0x40 <= ord(c) <= 0x7E:
                    break
            final = seq[-1:] if seq else ""
            if final == "~":
                return _CSI_TILDE.get(seq[:-1].split(";")[0], "")
            return _CSI_FINAL.get(final, "")
        if byte >= 0xC0:  # multibyte UTF-8
            need = 1 if byte < 0xE0 else 2 if byte < 0xF0 else 3
            data = first
            for _ in range(need):
                data += self._posix_byte()
            return data.decode("utf-8", errors="replace")
        return _simple(first.decode("latin-1"))

    # -- Windows ---------------------------------------------------------
    def _read_windows(self, timeout: float | None) -> str | None:
        if timeout is not None:
            deadline = time.monotonic() + timeout
            while not msvcrt.kbhit():  # type: ignore[attr-defined]
                if time.monotonic() >= deadline:
                    return None
                time.sleep(0.02)
        ch = msvcrt.getwch()  # type: ignore[attr-defined]
        if ch in ("\x00", "\xe0"):
            return _WIN_SPECIAL.get(msvcrt.getwch(), "")  # type: ignore[attr-defined]
        if ch == "\x1b":
            return "esc"
        return _simple(ch)

    def read(self, timeout: float | None = None) -> str | None:
        """Block for a key (or ``timeout`` seconds -> ``None``). Unknown keys return ``""``."""
        if IS_WINDOWS:
            return self._read_windows(timeout)
        return self._read_posix(timeout)
