import json
import re
from pathlib import Path

from uswap.utils import i18n
from uswap.utils.i18n import t

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / "uswap" / "locales"


def _load(name):
    return json.loads((LOCALES / f"{name}.json").read_text(encoding="utf-8"))


def test_locales_have_identical_keys():
    assert set(_load("en")) == set(_load("es"))


def test_placeholders_match_between_languages():
    en, es = _load("en"), _load("es")
    ph = re.compile(r"{(\w+)}")
    for key in en:
        assert set(ph.findall(en[key])) == set(ph.findall(es[key])), key


def test_every_key_used_in_code_exists():
    en = _load("en")
    pattern = re.compile(r"""\bt\(\s*['"]([a-z_]+(?:\.[a-z_]+)+)['"]""")
    hint = re.compile(r"""['"](hint\.[a-z_]+)['"]""")
    used = set()
    for path in (ROOT / "uswap").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        used |= set(pattern.findall(text)) | set(hint.findall(text))
    missing = sorted(k for k in used if k not in en)
    assert not missing, missing


def test_dynamic_keys_exist():
    en = _load("en")
    for dep in ("image", "watcher", "ui", "media", "document", "pdf"):
        assert f"dep.{dep}" in en
    for k in (
        "language",
        "theme",
        "glyphs",
        "out_mode",
        "out_dir",
        "naming",
        "suffix",
        "quality",
        "workers",
        "rules",
    ):
        assert f"cfg.{k}" in en


def test_switching_and_fallback():
    i18n.set_language("es")
    assert t("menu.quit") == "Salir"
    i18n.set_language("en")
    assert t("menu.quit") == "Quit"
    assert t("does.not.exist") == "does.not.exist"
    assert t("popup.done", secs="1.0") == "Done in 1.0s"
    assert i18n.set_language("xx") == "en"


def test_auto_detects_from_env(monkeypatch):
    monkeypatch.setenv("USWAP_LANG", "es_ES.UTF-8")
    assert i18n.set_language("auto") == "es"
