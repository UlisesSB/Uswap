import shutil
import wave

import pytest
from PIL import Image

from uswap.utils import i18n
from uswap.utils.config import Config


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("USWAP_CONFIG_DIR", str(tmp_path / "cfg"))
    i18n.set_language("en")


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def png(tmp_path):
    p = tmp_path / "pic.png"
    Image.new("RGBA", (120, 80), (255, 0, 0, 128)).save(p)
    return p


@pytest.fixture
def wav(tmp_path):
    p = tmp_path / "tone.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x10" * 4000)
    return p


def needs(binary):
    return pytest.mark.skipif(shutil.which(binary) is None, reason=f"{binary} not installed")
