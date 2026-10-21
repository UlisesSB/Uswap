import zipfile

from PIL import Image

from uswap.core import detector


def test_png_by_magic_even_with_wrong_extension(tmp_path, png):
    fake = tmp_path / "photo.jpg"
    fake.write_bytes(png.read_bytes())
    info = detector.detect(fake)
    assert info.ext == "png" and info.verified and info.mismatch
    assert "jpg" in info.targets or "webp" in info.targets


def test_aliases_do_not_count_as_mismatch(tmp_path):
    p = tmp_path / "a.jpeg"
    Image.new("RGB", (4, 4)).save(p, "JPEG")
    info = detector.detect(p)
    assert info.ext == "jpg" and not info.mismatch


def test_wav_and_riff_family(wav):
    assert detector.detect(wav).ext == "wav"


def test_zip_based_documents(tmp_path):
    docx = tmp_path / "x.docx"
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr("word/document.xml", "<w/>")
    assert detector.detect(docx).ext == "docx"

    odt = tmp_path / "x.odt"
    with zipfile.ZipFile(odt, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.text")
    assert detector.detect(odt).ext == "odt"

    epub = tmp_path / "x.epub"
    with zipfile.ZipFile(epub, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
    assert detector.detect(epub).ext == "epub"

    plain = tmp_path / "x.zip"
    with zipfile.ZipFile(plain, "w") as z:
        z.writestr("a.txt", "hi")
    assert not detector.detect(plain).supported


def test_container_variants():
    base = b"\x00\x00\x00\x18ftyp"
    assert detector.sniff(None, base + b"M4A \x00") == "m4a"
    assert detector.sniff(None, base + b"qt  \x00") == "mov"
    assert detector.sniff(None, base + b"isom\x00") == "mp4"
    assert detector.sniff(None, b"\x1a\x45\xdf\xa3" + b"\x00" * 10 + b"webm") == "webm"
    assert detector.sniff(None, b"\x1a\x45\xdf\xa3" + b"\x00" * 10 + b"matroska") == "mkv"
    assert detector.sniff(None, b"OggS" + b"\x00" * 20 + b"OpusHead") == "opus"
    assert detector.sniff(None, b"OggS" + b"\x00" * 20 + b"vorbis") == "ogg"
    assert detector.sniff(None, b"ID3\x04\x00") == "mp3"
    assert detector.sniff(None, b"\xff\xfb\x90\x00") == "mp3"
    assert detector.sniff(None, b"\xff\xf1\x50\x80") == "aac"
    assert detector.sniff(None, b"fLaC\x00") == "flac"
    assert detector.sniff(None, b"%PDF-1.7") == "pdf"
    assert detector.sniff(None, b"{\\rtf1\\ansi") == "rtf"
    assert detector.sniff(None, b"  <!DOCTYPE html><html>") == "html"


def test_text_formats_trust_extension(tmp_path):
    md = tmp_path / "n.md"
    md.write_text("# hello\n", encoding="utf-8")
    assert detector.detect(md).ext == "md"
    binary_named_md = tmp_path / "b.md"
    binary_named_md.write_bytes(b"\x00\x01\x02\x03")
    assert not detector.detect(binary_named_md).supported


def test_text_renamed_to_binary_extension_is_rejected(tmp_path):
    p = tmp_path / "fake.png"
    p.write_text("not an image", encoding="utf-8")
    assert not detector.detect(p).supported


def test_unknown_missing_and_directory(tmp_path):
    assert not detector.detect(tmp_path / "nope.png").supported
    assert not detector.detect(tmp_path).supported
    blob = tmp_path / "x.xyz"
    blob.write_bytes(b"\x00\xff\x00\xff")
    assert not detector.detect(blob).supported


def test_common_targets(tmp_path, png):
    other = tmp_path / "o.png"
    other.write_bytes(png.read_bytes())
    a, b = detector.detect(png), detector.detect(other)
    assert detector.common_targets([a, b]) == a.targets
    md = tmp_path / "n.md"
    md.write_text("x")
    assert detector.common_targets([a, detector.detect(md)]) == []
