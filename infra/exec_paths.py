from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional


def _project_root() -> Path:
    # infra/exec_paths.py -> project root is parent of 'infra'
    return Path(__file__).resolve().parents[1]


def _is_executable(p: Path) -> bool:
    if not p.is_file():
        return False
    if os.name == "nt":
        return p.suffix.lower() in (".exe", ".bat", ".cmd")
    return os.access(str(p), os.X_OK)


def _candidate_paths(base_names: list[str]) -> list[Path]:
    """Return plausible locations inside the repo for bundled binaries."""
    root = _project_root()
    bins: list[Path] = []
    # Common spots to check
    for d in (
        root / "bin",
        root / "vendor" / "ffmpeg" / "bin",
        root / "tools" / "ffmpeg" / "bin",
    ):
        for name in base_names:
            bins.append(d / name)
    return bins


def resolve_executable(env_var: str, program_name: str) -> Optional[str]:
    """Resolve an executable path with overrides and fallbacks.

    Resolution order:
    1) Explicit path via env var (if points to a valid file)
    2) System PATH via shutil.which
    3) Bundled locations inside the repo (bin/, vendor/ffmpeg/bin, tools/ffmpeg/bin)
    """
    # 1) Environment override
    override = os.getenv(env_var)
    if override:
        p = Path(override).expanduser()
        if _is_executable(p):
            return str(p)
        # On Windows, allow omitting .exe in override
        if os.name == "nt" and p.suffix == "" and _is_executable(p.with_suffix(".exe")):
            return str(p.with_suffix(".exe"))

    # 2) System PATH
    found = shutil.which(program_name)
    if found:
        return found

    # 3) Bundled locations in repo
    base_names = [program_name]
    if os.name == "nt":
        base_names = [f"{program_name}.exe", program_name]
    for cand in _candidate_paths(base_names):
        if _is_executable(cand):
            return str(cand)

    return None


def get_ffmpeg_exe() -> Optional[str]:
    return resolve_executable("KNOTZFLIX_FFMPEG", "ffmpeg")


def get_ffprobe_exe() -> Optional[str]:
    return resolve_executable("KNOTZFLIX_FFPROBE", "ffprobe")

