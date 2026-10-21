import pytest
from PIL import Image

from tests.conftest import needs
from uswap.core import converter, detector
from uswap.core.converter import convert_file, resolve_output, unique_path
from uswap.core.engine_doc import PANDOC_READER


@pytest.mark.parametrize("target", ["jpg", "webp", "bmp", "gif", "tiff", "ico", "pdf"])
def test_image_targets(png, config, target):
    res = convert_file(png, target, config)
    assert res.ok, res.error
    assert res.outputs[0].exists() and res.outputs[0].suffix == f".{target}"
    if target != "pdf":
        with Image.open(res.outputs[0]) as img:
            assert img.format is not None


def test_jpg_flattens_alpha(png, config):
    res = convert_file(png, "jpg", config)
    with Image.open(res.outputs[0]) as img:
        assert img.mode == "RGB"


def test_same_format_is_skipped(png, config):
    res = convert_file(png, "png", config)
    assert res.ok and res.skipped


def test_unsupported_and_no_route(tmp_path, png, config):
    junk = tmp_path / "x.xyz"
    junk.write_bytes(b"\x00\xff")
    assert not convert_file(junk, "png", config).ok
    res = convert_file(png, "mp3", config)
    assert not res.ok and res.error.startswith("no_route")


def test_naming_rules(png, config):
    config.set("output.naming", "keep")
    assert resolve_output(png, "jpg", config).name == "pic.jpg"
    config.set("output.naming", "suffix")
    assert resolve_output(png, "jpg", config).name == "pic-converted.jpg"
    # existing target gets a numbered name unless overwrite is on
    (png.parent / "pic-converted.jpg").write_text("x")
    assert resolve_output(png, "jpg", config).name == "pic-converted (1).jpg"
    config.set("output.naming", "overwrite")
    assert resolve_output(png, "jpg", config).name == "pic.jpg"


def test_overwrite_replaces_existing_output(png, config):
    config.set("output.naming", "overwrite")
    (png.parent / "pic.jpg").write_text("old")
    res = convert_file(png, "jpg", config)
    assert res.ok and res.outputs[0].stat().st_size > 10


def test_never_clobbers_source(tmp_path, config):
    p = tmp_path / "a.jpg"
    Image.new("RGB", (8, 8)).save(p, "JPEG")
    config.set("output.naming", "overwrite")
    dst = resolve_output(p, "jpg", config)  # same name as source
    assert dst != p


def test_custom_output_dir(png, config, tmp_path):
    config.set("output.mode", "custom")
    config.set("output.custom_dir", str(tmp_path / "out"))
    res = convert_file(png, "webp", config)
    assert res.ok and res.outputs[0].parent == tmp_path / "out"


def test_unique_path(tmp_path):
    p = tmp_path / "a.txt"
    assert unique_path(p) == p
    p.write_text("x")
    assert unique_path(p).name == "a (1).txt"


def test_progress_callback(png, config):
    seen = []
    convert_file(png, "jpg", config, progress=seen.append)
    assert seen and seen[-1] == 1.0


@needs("ffmpeg")
def test_audio_conversion(wav, config):
    seen = []
    res = convert_file(wav, "mp3", config, progress=seen.append)
    assert res.ok, res.error
    assert detector.detect(res.outputs[0]).ext == "mp3"
    assert seen[-1] == 1.0


@needs("ffmpeg")
def test_ffmpeg_failure_is_reported(tmp_path, config):
    bad = tmp_path / "bad.wav"
    bad.write_bytes(b"RIFF\x00\x00\x00\x00WAVEgarbage")
    res = convert_file(bad, "mp3", config)
    assert not res.ok and res.error
    assert not (tmp_path / "bad.mp3").exists()


@needs("pandoc")
def test_markdown_to_docx_and_back(tmp_path, config):
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\nHello **world**\n", encoding="utf-8")
    res = convert_file(md, "docx", config)
    assert res.ok, res.error
    assert detector.detect(res.outputs[0]).ext == "docx"
    config.set("output.naming", "suffix")
    back = convert_file(res.outputs[0], "md", config)
    assert back.ok and "world" in back.outputs[0].read_text(encoding="utf-8")


@needs("pdftoppm")
def test_pdf_to_png_and_txt(png, config):
    pdf = convert_file(png, "pdf", config).outputs[0]
    res = convert_file(pdf, "png", config)
    assert res.ok and res.outputs[0].suffix == ".png"
    assert convert_file(pdf, "txt", config).ok


def test_format_error_translation():
    from uswap.utils.i18n import t

    assert "ffmpeg" in converter.format_error("missing:ffmpeg", t)
    assert converter.format_error("boom", t) == "boom"


def test_all_pandoc_readers_have_known_ext():
    from uswap.core import formats

    assert set(PANDOC_READER) <= set(formats.FORMATS)
