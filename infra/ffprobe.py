from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class MediaInfo:
    codec_name: Optional[str]
    width: Optional[int]
    height: Optional[int]
    duration_sec: Optional[float]
    channels: Optional[int]


def parse_ffprobe_json(data: dict[str, Any]) -> MediaInfo:
    fmt = data.get("format", {}) or {}
    duration = None
    try:
        duration = float(fmt.get("duration")) if fmt.get("duration") is not None else None
    except (TypeError, ValueError):
        duration = None

    codec = None
    width = None
    height = None
    channels = None
    for stream in data.get("streams", []) or []:
        if stream.get("codec_type") == "video" and codec is None:
            codec = stream.get("codec_name")
            width = stream.get("width")
            height = stream.get("height")
        if stream.get("codec_type") == "audio" and channels is None:
            channels = stream.get("channels")
    return MediaInfo(codec_name=codec, width=width, height=height, duration_sec=duration, channels=channels)


def probe(path: Path, timeout_sec: int = 10) -> Optional[MediaInfo]:
    """Run ffprobe on a media file, returning parsed MediaInfo or None on failure.

    Requires ffprobe to be present on PATH or configured. This function never raises on failure.
    """
    exe = get_ffprobe_exe()
    if not exe:
        return None
    try:
        result = subprocess.run(
            [
                exe,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        return parse_ffprobe_json(data)
    except Exception:
        from .exec_paths import get_ffprobe_exe
        return None
