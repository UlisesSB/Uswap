"""JSON configuration manager.

The config lives in a per-user directory:

* Windows: ``%APPDATA%\\uswap\\config.json``
* Linux/macOS: ``$XDG_CONFIG_HOME/uswap/config.json`` (default ``~/.config/uswap``)

Unknown keys are preserved, missing keys are filled from :data:`DEFAULTS`, and a
corrupt file is moved aside (``config.json.bak``) instead of crashing the app.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "language": "auto",  # auto | en | es
    "theme": "gruvbox",  # gruvbox | nord | catppuccin | tokyo-night | monokai
    "glyphs": "unicode",  # unicode | ascii
    "output": {
        "mode": "same",  # same | custom | downloads
        "custom_dir": "",
        "naming": "keep",  # keep | suffix | overwrite
        "suffix": "-converted",
    },
    "quality": {
        "image": 90,  # 1-100 (jpg / webp)
    },
    "batch": {
        "workers": 4,
    },
    "quick_popup": {
        "auto_close": True,
        "close_delay": 0.8,
    },
    "watcher": {
        "recursive": False,
        # {"match": "png" | "image" | "*", "target": "webp"}
        "rules": [],
    },
}

CHOICES: dict[str, list[str]] = {
    "language": ["auto", "en", "es"],
    "theme": ["gruvbox", "nord", "catppuccin", "tokyo-night", "monokai"],
    "glyphs": ["unicode", "ascii"],
    "output.mode": ["same", "custom", "downloads"],
    "output.naming": ["keep", "suffix", "overwrite"],
}


def config_dir() -> Path:
    """Return the per-user configuration directory (not created)."""
    override = os.environ.get("USWAP_CONFIG_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "uswap"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "uswap"


def _merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    """Recursively overlay ``extra`` onto ``base`` (returns a new dict)."""
    out = copy.deepcopy(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


class Config:
    """Thin wrapper around the settings dict with dotted-key access."""

    def __init__(self, data: dict[str, Any] | None = None, path: Path | None = None):
        self.path = path
        self.data: dict[str, Any] = _merge(DEFAULTS, data or {})

    # -- persistence -----------------------------------------------------
    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        path = path or (config_dir() / "config.json")
        data: dict[str, Any] = {}
        if path.is_file():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("config root must be an object")
                data = loaded
            except (OSError, ValueError):
                try:
                    path.replace(path.with_suffix(".json.bak"))
                except OSError:
                    pass
        return cls(data, path)

    def save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    # -- access ----------------------------------------------------------
    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        node = self.data
        for part in parts[:-1]:
            if not isinstance(node.get(part), dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value

    def copy(self) -> Config:
        clone = Config(copy.deepcopy(self.data), self.path)
        return clone

    # -- helpers ---------------------------------------------------------
    def output_dir_for(self, src: Path) -> Path:
        """Resolve the directory where the converted file for ``src`` goes."""
        mode = self.get("output.mode", "same")
        if mode == "custom":
            custom = str(self.get("output.custom_dir", "")).strip()
            if custom:
                return Path(custom).expanduser()
        elif mode == "downloads":
            return Path.home() / "Downloads"
        return src.parent
