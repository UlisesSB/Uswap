import time

import pytest
from PIL import Image

from uswap.core import detector
from uswap.watcher.monitor import FolderMonitor, Rule, rules_from_config


def test_rule_parse_and_match(png):
    info = detector.detect(png)
    assert Rule.parse("png:webp").applies_to(info)
    assert Rule.parse("image:jpeg").target == "jpg"
    assert Rule.parse("*:webp").applies_to(info)
    assert not Rule.parse("mp3:wav").applies_to(info)
    with pytest.raises(ValueError):
        Rule.parse("nonsense")


def test_rules_from_config(config):
    config.set("watcher.rules", [{"match": "PNG", "target": "webp"}, {"bad": 1}])
    rules = rules_from_config(config)
    assert len(rules) == 1 and rules[0].match == "png"


def _wait(cond, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.2)
    return False


def test_monitor_converts_new_files_without_loops(tmp_path, config):
    mon = FolderMonitor(tmp_path, config, [Rule("image", "webp"), Rule("webp", "jpg")])
    mon.start()
    try:
        time.sleep(0.5)
        Image.new("RGB", (16, 16), (1, 2, 3)).save(tmp_path / "new.png")
        assert _wait(lambda: (tmp_path / "new.webp").exists() and mon.counts["ok"] >= 1)
        time.sleep(2)  # give a (wrong) chained conversion the chance to happen
        assert not (tmp_path / "new.jpg").exists()
        assert mon.counts["ok"] == 1
        (tmp_path / "junk.bin").write_bytes(b"\x00\x01\x02")
        assert _wait(lambda: mon.counts["skipped"] >= 1)
    finally:
        mon.stop()
