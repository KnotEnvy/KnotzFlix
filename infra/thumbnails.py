from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .cache import content_addressed_path
from .exec_paths import get_ffmpeg_exe
import hashlib
import random
import re


# Valid 1x1 PNG bytes (RGBA), reliably loadable by Qt.
PLACEHOLDER_PNG = bytes(
    [
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR
        0x00, 0x00, 0x00, 0x01,  # width = 1
        0x00, 0x00, 0x00, 0x01,  # height = 1
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89,
        0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41, 0x54,  # IDAT
        0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00, 0x05, 0x00, 0x01,
        0x0D, 0x0A, 0x2D, 0xB4,
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,  # IEND
        0xAE, 0x42, 0x60, 0x82,
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


def choose_timestamp_deterministic(file_fingerprint: str, duration_sec: Optional[float]) -> float:
    """Choose a poster timestamp deterministically based on file fingerprint.

    Uses a baseline of 20% into the video, with a tiny deterministic offset
    derived from the fingerprint to avoid always picking the exact same frame
    across many files of similar length. Clamped safely within [10s, duration-5s].
    """
    base = pick_timestamp(duration_sec)
    if not duration_sec or duration_sec <= 0:
        return base
    # Derive a stable pseudo-random offset in seconds within [-3s, +3s]
    h = hashlib.blake2b(file_fingerprint.encode("utf-8"), digest_size=4).digest()
    n = int.from_bytes(h, "big")
    # map to [-1.0, +1.0]
    unit = (n / 0xFFFFFFFF) * 2.0 - 1.0
    offset = unit * 3.0
    ts = base + offset
    ts = max(10.0, min(ts, max(duration_sec - 5.0, 0.0)))
    return ts


def choose_candidate_timestamps(file_fingerprint: str, duration_sec: Optional[float], *, count: int = 5) -> list[float]:
    """Return a deterministic list of candidate timestamps for poster selection.

    - Always includes the base deterministic timestamp.
    - Adds jittered offsets around the base using a PRNG seeded by the fingerprint.
    - Clamps each candidate within [10s, duration-5s] (or 15s baseline if no duration).
    - Returns increasing order and de-duplicates.
    """
    if not duration_sec or duration_sec <= 0:
        # No duration; fall back to a single sensible default
        return [pick_timestamp(duration_sec)]

    base = choose_timestamp_deterministic(file_fingerprint, duration_sec)
    rng = random.Random()
    # Seed using a stable hash of the fingerprint
    seed = int.from_bytes(hashlib.blake2b(file_fingerprint.encode("utf-8"), digest_size=8).digest(), "big")
    rng.seed(seed)

    # Generate symmetric jitter values in seconds within ~[-8s, +8s]
    # Bias toward moderate offsets to avoid near-identical frames
    candidates = {round(base, 2)}
    for _ in range(max(0, count - 1)):
        # Triangular distribution for more mid offsets
        off = (rng.random() + rng.random() - 1.0) * 8.0
        t = base + off
        # Clamp to safe range
        t = max(10.0, min(t, max(duration_sec - 5.0, 10.0)))
        candidates.add(round(t, 2))
        if len(candidates) >= count:
            break

    res = sorted(candidates)
    return res


def _parse_signalstats(text: str) -> dict[str, float]:
    """Parse ffmpeg signalstats output for a single frame.

    Returns keys like YAVG, YMIN, YMAX if found; values 0..255.
    """
    # Search the last occurrence to ensure we get the final frame
    last_line = ""
    for line in text.splitlines():
        if "signalstats" in line:
            last_line = line
    res: dict[str, float] = {}
    if last_line:
        for key in ("YAVG", "YMIN", "YMAX"):
            m = re.search(rf"{key}:\s*([0-9]+(?:\.[0-9]+)?)", last_line)
            if m:
                try:
                    res[key] = float(m.group(1))
                except Exception:
                    pass
    return res


def _ffmpeg_signalstats(media_path: Path, ts_sec: float, *, filter_chain: str) -> dict[str, float]:
    exe = get_ffmpeg_exe()
    if not exe:
        return {}
    cmd = [
        exe,
        "-hide_banner",
        "-nostdin",
        "-ss",
        f"{ts_sec:.2f}",
        "-i",
        str(media_path),
        "-frames:v",
        "1",
        "-vf",
        filter_chain,
        "-f",
        "null",
        "-",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        out = (res.stdout or "") + "\n" + (res.stderr or "")
        return _parse_signalstats(out)
    except Exception:
        return {}


def _score_timestamp(media_path: Path, ts_sec: float) -> Optional[float]:
    """Compute a heuristic score for a frame at ts.

    Considers mid-brightness preference, dynamic range, and edge strength.
    Returns None if scoring fails.
    """
    # Base frame stats at small scale for speed
    base = _ffmpeg_signalstats(media_path, ts_sec, filter_chain="scale=-2:160,signalstats")
    if not base:
        return None
    yavg = base.get("YAVG")
    ymin = base.get("YMIN")
    ymax = base.get("YMAX")
    if yavg is None or ymin is None or ymax is None:
        return None
    # Edge strength via edgedetect then signalstats
    edge = _ffmpeg_signalstats(
        media_path,
        ts_sec,
        filter_chain="scale=-2:160,edgedetect=low=0.08:high=0.25,signalstats",
    )
    edge_yavg = edge.get("YAVG", 0.0)

    # Normalize into [0,1]
    # Mid-brightness score peaks around 128 (8-bit luma)
    midness = max(0.0, 1.0 - abs((yavg - 128.0) / 112.0))  # 112 ~ half of 224 range
    dyn_range = max(0.0, min(1.0, (ymax - ymin) / 255.0))
    edge_strength = max(0.0, min(1.0, edge_yavg / 255.0))

    # Weighted sum
    score = 0.5 * midness + 0.3 * edge_strength + 0.2 * dyn_range
    return float(score)


def build_ffmpeg_cmd(input_path: Path, out_path: Path, ts_sec: float, height: int, quality: int) -> list[str]:
    # Ensure even dimensions for codecs
    vf = f"scale=-2:{height}"
    return [
        get_ffmpeg_exe() or "ffmpeg",
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
        get_ffmpeg_exe() or "ffmpeg",
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
    force: bool = False,
) -> tuple[Path, Optional[list[str]]]:
    out = content_addressed_path("poster", file_fingerprint, f"h{spec.height}", "jpg")
    if out.exists() and not force:
        return out, None

    # Prefer heuristic via ffmpeg 'thumbnail' filter; fallback to timestamp(s) if it fails
    thumb_cmd = build_ffmpeg_cmd_thumbnail(media_path, out, spec.height, spec.jpeg_quality)
    ts = choose_timestamp_deterministic(file_fingerprint, duration_sec)
    ts_cmd = build_ffmpeg_cmd(media_path, out, ts, spec.height, spec.jpeg_quality)
    if dry_run:
        # For tests, expose the timestamp-based command shape (deterministic ts)
        return out, ts_cmd

    if get_ffmpeg_exe():
        # Try thumbnail heuristic first
        try:
            res = subprocess.run(thumb_cmd, capture_output=True, text=True, timeout=30)
            if res.returncode == 0 and out.exists():
                return out, None
        except Exception:
            pass

        # Score candidates and pick the best
        candidates = choose_candidate_timestamps(file_fingerprint, duration_sec, count=5)
        scored: list[tuple[float, float]] = []  # (score, ts)
        for ts_i in candidates:
            s = _score_timestamp(media_path, ts_i)
            if s is not None:
                scored.append((s, ts_i))

        if scored:
            # Pick highest score, stabilize ordering by ts for ties
            scored.sort(key=lambda t: (t[0], t[1]))
            best_ts = scored[-1][1]
            try:
                cmd = build_ffmpeg_cmd(media_path, out, best_ts, spec.height, spec.jpeg_quality)
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if res.returncode == 0 and out.exists():
                    return out, None
            except Exception:
                pass

        # If scoring failed, fall back to trying candidates in order
        for ts_i in candidates:
            try:
                cmd = build_ffmpeg_cmd(media_path, out, ts_i, spec.height, spec.jpeg_quality)
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if res.returncode == 0 and out.exists():
                    return out, None
            except Exception:
                continue

    # Fallback: write placeholder PNG bytes to the computed path (extension is .jpg but Qt loads by signature)
    out.write_bytes(PLACEHOLDER_PNG)
    return out, None


def detect_poster_source(path: Path) -> str:
    """Best-effort classify poster source for DB metadata.

    Returns 'placeholder' if file looks like our tiny PNG placeholder; otherwise 'ffmpeg'.
    """
    try:
        data = path.read_bytes()
        if len(data) <= 2048 and data[:8] == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]):
            return "placeholder"
    except Exception:
        pass
    return "ffmpeg"


def ffmpeg_status() -> tuple[bool, str]:
    """Return (available, version_string)."""
    exe = get_ffmpeg_exe()
    if not exe:
        return False, "ffmpeg not found"
    try:
        res = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=3)
        head = (res.stdout or res.stderr or "").splitlines()[:1]
        return True, head[0] if head else "ffmpeg (version unknown)"
    except Exception:
        return True, "ffmpeg (version unknown)"
