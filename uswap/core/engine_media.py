"""Audio/video engine (FFmpeg through ``subprocess``)."""

from __future__ import annotations

import re
import shutil
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from uswap.core.errors import Cancelled, ConversionError, MissingDependency
from uswap.utils.system import subprocess_flags

_X264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"]
_AAC = ["-c:a", "aac", "-b:a", "160k"]

# target -> ffmpeg output arguments
ARGS: dict[str, list[str]] = {
    # audio
    "mp3": ["-vn", "-c:a", "libmp3lame", "-q:a", "2"],
    "wav": ["-vn", "-c:a", "pcm_s16le"],
    "flac": ["-vn", "-c:a", "flac"],
    "ogg": ["-vn", "-c:a", "libvorbis", "-q:a", "5"],
    "opus": ["-vn", "-c:a", "libopus", "-b:a", "128k"],
    "aac": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    "m4a": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    # video
    "mp4": [*_X264, *_AAC, "-movflags", "+faststart"],
    "mkv": [*_X264, *_AAC],
    "mov": [*_X264, *_AAC],
    "webm": ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-c:a", "libopus", "-b:a", "128k"],
    "avi": ["-c:v", "mpeg4", "-q:v", "4", "-c:a", "libmp3lame", "-q:a", "4"],
    "gif": ["-an", "-vf", "fps=12,scale=480:-1:flags=lanczos", "-loop", "0"],
}

_PROGRESS_KEYS = re.compile(
    r"^(frame|fps|stream_\d+_\d+_q|bitrate|total_size|out_time_us|out_time_ms|out_time|"
    r"dup_frames|drop_frames|speed|progress)=",
)


def _duration(src: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return 0.0
    try:
        out = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(src),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            **subprocess_flags(),
        )
        return float(out.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0


def convert(
    src: Path,
    dst: Path,
    target: str,
    *,
    progress: Callable[[float], None] | None = None,
    cancel: threading.Event | None = None,
) -> list[Path]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise MissingDependency("ffmpeg")
    if target not in ARGS:
        raise ConversionError(f"unsupported media target: {target}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    total = _duration(src)
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostats",
        "-progress",
        "pipe:1",
        "-i",
        str(src),
        *ARGS[target],
        str(dst),
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        **subprocess_flags(),
    )
    errors: list[str] = []
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            if cancel is not None and cancel.is_set():
                proc.kill()
                raise Cancelled("cancelled")
            line = line.strip()
            if not line:
                continue
            if _PROGRESS_KEYS.match(line):
                key, _, value = line.partition("=")
                if key in ("out_time_us", "out_time_ms") and total > 0 and progress:
                    try:
                        seconds = int(value) / 1_000_000
                    except ValueError:
                        continue
                    progress(min(max(seconds / total, 0.0), 0.99))
            else:
                errors.append(line)
        code = proc.wait()
    except BaseException:
        proc.kill()
        proc.wait()
        dst.unlink(missing_ok=True)
        raise
    if code != 0:
        dst.unlink(missing_ok=True)
        detail = "\n".join(errors[-6:]) or f"ffmpeg exited with code {code}"
        raise ConversionError(detail)
    if progress:
        progress(1.0)
    return [dst]
