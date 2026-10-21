import json

from uswap.utils.config import DEFAULTS, Config, config_dir


def test_defaults_and_dotted_access():
    c = Config()
    assert c.get("output.naming") == "keep"
    assert c.get("missing.key", "x") == "x"
    c.set("output.naming", "suffix")
    c.set("new.deep.key", 1)
    assert c.get("output.naming") == "suffix" and c.get("new.deep.key") == 1
    assert DEFAULTS["output"]["naming"] == "keep"  # defaults not mutated


def test_save_and_load_roundtrip_and_merge(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"theme": "nord", "output": {"naming": "suffix"}}))
    c = Config.load(path)
    assert c.get("theme") == "nord"
    assert c.get("output.mode") == "same"  # filled from defaults
    c.set("language", "es")
    c.save()
    assert json.loads(path.read_text())["language"] == "es"


def test_corrupt_file_is_backed_up(tmp_path):
    path = tmp_path / "c.json"
    path.write_text("{not json")
    c = Config.load(path)
    assert c.get("theme") == "gruvbox"
    assert (tmp_path / "c.json.bak").exists()


def test_output_dir_modes(tmp_path):
    src = tmp_path / "a" / "f.png"
    c = Config()
    assert c.output_dir_for(src) == src.parent
    c.set("output.mode", "custom")
    c.set("output.custom_dir", str(tmp_path / "out"))
    assert c.output_dir_for(src) == tmp_path / "out"
    c.set("output.mode", "downloads")
    assert c.output_dir_for(src).name == "Downloads"


def test_config_dir_env_override(tmp_path):
    assert config_dir() == tmp_path / "cfg"
