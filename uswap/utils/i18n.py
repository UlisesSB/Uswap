"""Tiny translation engine (EN/ES) backed by JSON files in ``uswap/locales``."""

from __future__ import annotations

import json
import locale
import os
from pathlib import Path
from typing import Any

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
SUPPORTED = ("en", "es")
DEFAULT_LANG = "en"

_strings: dict[str, str] = {}
_fallback: dict[str, str] = {}
_current = DEFAULT_LANG


def _load(lang: str) -> dict[str, str]:
    path = LOCALES_DIR / f"{lang}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def detect_system_language() -> str:
    """Best-effort guess of the user's language, limited to SUPPORTED."""
    candidates = [os.environ.get(v) for v in ("USWAP_LANG", "LC_ALL", "LC_MESSAGES", "LANG")]
    try:
        candidates.append(locale.getlocale()[0])
    except (ValueError, TypeError):
        pass
    for cand in candidates:
        if cand:
            code = cand.replace("-", "_").split("_")[0].lower()
            if code in SUPPORTED:
                return code
    return DEFAULT_LANG


def set_language(lang: str | None) -> str:
    """Activate ``lang`` ("auto" detects it). Returns the language actually used."""
    global _strings, _fallback, _current
    if not lang or lang == "auto":
        lang = detect_system_language()
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    _fallback = _load(DEFAULT_LANG)
    _strings = _fallback if lang == DEFAULT_LANG else _load(lang)
    _current = lang
    return lang


def current_language() -> str:
    return _current


def t(key: str, **kwargs: Any) -> str:
    """Translate ``key``; falls back to English, then to the key itself."""
    if not _fallback:
        set_language("auto")
    text = _strings.get(key) or _fallback.get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text
