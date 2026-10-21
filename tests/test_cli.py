import pytest
from PIL import Image

from uswap import __version__, cli


def test_version(capsys):
    assert cli.main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out


def test_headless_convert(png, capsys):
    assert cli.main([str(png), "--to", "jpg"]) == 0
    assert (png.parent / "pic.jpg").exists()
    assert "pic.jpg" in capsys.readouterr().out


def test_headless_glob_and_output_dir(tmp_path):
    for n in ("a", "b"):
        Image.new("RGB", (8, 8)).save(tmp_path / f"{n}.png")
    out = tmp_path / "out"
    assert cli.main([str(tmp_path / "*.png"), "--to", "webp", "-o", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["a.webp", "b.webp"]


def test_directory_argument(tmp_path):
    Image.new("RGB", (8, 8)).save(tmp_path / "a.png")
    (tmp_path / "skip.bin").write_bytes(b"\x00\x01")
    assert cli.main([str(tmp_path), "--to", "jpg"]) == 1  # skip.bin fails, a.png converts
    assert (tmp_path / "a.jpg").exists()


def test_errors_exit_codes(tmp_path, png):
    assert cli.main([str(tmp_path / "missing.png"), "--to", "jpg"]) == 2
    assert cli.main([str(png), "--to", "nope"]) == 2


def test_formats_and_doctor(capsys):
    assert cli.main(["--formats"]) == 0
    assert "png" in capsys.readouterr().out
    assert cli.main(["--doctor"]) in (0, 1)


def test_interactive_modes_refuse_without_tty(png):
    assert cli.main([str(png)]) == 2
    assert cli.main([]) == 2


def test_expand_inputs(tmp_path):
    (tmp_path / "a.png").write_bytes(b"x")
    files, missing = cli.expand_inputs(
        [str(tmp_path / "*.png"), str(tmp_path / "zzz*.png"), "nope.txt"]
    )
    assert [f.name for f in files] == ["a.png"]
    assert len(missing) == 2


def test_parser_rejects_bad_lang():
    with pytest.raises(SystemExit):
        cli.main(["--lang", "xx"])
