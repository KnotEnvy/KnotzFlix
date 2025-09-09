from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .cache import content_addressed_path


# Minimal valid 1x1 JPEG bytes (JFIF), for placeholder generation without PIL.
PLACEHOLDER_JPEG = bytes(
    [
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x01, 0x00, 0x60, 0x00, 0x60, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00,
    ]
    + [0x08] * 64
    + [
        0xFF, 0xDB, 0x00, 0x43, 0x01,
    ]
    + [0x08] * 64
    + [
        0xFF, 0xC0, 0x00, 0x11, 0x08, 0x00, 0x01, 0x00, 0x01, 0x03, 0x01, 0x11,
        0x00, 0x02, 0x11, 0x01, 0x03, 0x11, 0x01, 0xFF, 0xC4, 0x00, 0x14, 0x00,
        0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0xFF, 0xDA, 0x00, 0x0C, 0x03, 0x01, 0x00, 0x02, 0x11,
        0x03, 0x11, 0x00, 0x3F, 0x00, 0xFF, 0xD9,
    ]
)


@dataclass
class PosterSpec:
    height: int = 1000
    jpeg_quality: int = 90


def pick_timestamp(duration_sec: Optional[float]) -> float:
    if not duration_sec or duration_sec <= 0:
        return 15.0
    ts = duration_sec * 0.2
    # clamp between 10s and duration-5s
    ts = max(10.0, min(ts, max(duration_sec - 5.0, 0.0)))
    return ts


def build_ffmpeg_cmd(input_path: Path, out_path: Path, ts_sec: float, height: int, quality: int) -> list[str]:
    # Ensure even dimensions for codecs
    vf = f"scale=-2:{height}"
    return [
        "ffmpeg",
        "-y",
        "-ss",
        f"{ts_sec:.2f}",
        "-i",
        str(input_path),
        "-frames:v",
        "1",
        "-vf",
        vf,
        "-q:v",
        str(max(2, min(quality // 10, 31))),
        str(out_path),
    ]


def build_ffmpeg_cmd_thumbnail(input_path: Path, out_path: Path, height: int, quality: int) -> list[str]:
    # Use ffmpeg's thumbnail filter to pick a representative frame automatically.
    vf = f"thumbnail,scale=-2:{height}"
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-frames:v",
        "1",
        "-vf",
        vf,
        "-q:v",
        str(max(2, min(quality // 10, 31))),
        str(out_path),
    ]


def generate_poster(
    media_path: Path,
    file_fingerprint: str,
    duration_sec: Optional[float],
    spec: PosterSpec = PosterSpec(),
    *,
    dry_run: bool = False,
) -> tuple[Path, Optional[list[str]]]:
    out = content_addressed_path("poster", file_fingerprint, f"h{spec.height}", "jpg")
    if out.exists():
        return out, None

    # Prefer heuristic via ffmpeg 'thumbnail' filter; fallback to timestamp if it fails
    thumb_cmd = build_ffmpeg_cmd_thumbnail(media_path, out, spec.height, spec.jpeg_quality)
    ts = pick_timestamp(duration_sec)
    ts_cmd = build_ffmpeg_cmd(media_path, out, ts, spec.height, spec.jpeg_quality)
    if dry_run:
        # For tests, expose the timestamp-based command shape
        return out, ts_cmd

    if shutil.which("ffmpeg"):
        # Try thumbnail heuristic first
        for cmd in (thumb_cmd, ts_cmd):
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if res.returncode == 0 and out.exists():
                    return out, None
            except Exception:
                continue

    # Fallback: write placeholder JPEG
    out.write_bytes(PLACEHOLDER_JPEG)
    return out, None
