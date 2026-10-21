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


def test_bundled_tools_added_to_path_when_frozen(tmp_path, monkeypatch):
    import sys

    from uswap.utils import system

    exe = tmp_path / "app" / "uswap.exe"
    (tmp_path / "app" / "tools").mkdir(parents=True)
    exe.write_text("")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    monkeypatch.setenv("PATH", "/usr/bin")
    assert system.add_bundled_tools_to_path() == (tmp_path / "app" / "tools").resolve()
    assert str(tmp_path / "app" / "tools") in system.os.environ["PATH"].split(system.os.pathsep)


def test_bundled_tools_noop_when_not_frozen():
    from uswap.utils import system

    assert system.add_bundled_tools_to_path() is None
