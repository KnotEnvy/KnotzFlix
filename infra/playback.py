from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def _platform() -> str:
    if sys.platform.startswith("win"):
        return "win"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def build_launch_command(path: Path, platform: Optional[str] = None) -> List[str]:
    plat = platform or _platform()
    p = str(path)
    if plat == "win":
        # Use cmd start to delegate to default handler
        # start "" "path"
        return ["cmd", "/c", "start", "", p]
    elif plat == "darwin":
        return ["open", p]
    else:
        return ["xdg-open", p]


def build_reveal_command(path: Path, platform: Optional[str] = None) -> List[str]:
    plat = platform or _platform()
    p = str(path)
    if plat == "win":
        # explorer /select, "path"
        return ["explorer", "/select,", p]
    elif plat == "darwin":
        return ["open", "-R", p]
    else:
        # Open containing directory (normalize to POSIX-style separators)
        p_posix = p.replace("\\", "/")
        parent = p_posix.rsplit("/", 1)[0] if "/" in p_posix else p_posix
        return ["xdg-open", parent]


def launch_external(path: Path, dry_run: bool = False) -> bool | List[str]:
    cmd = build_launch_command(path)
    if dry_run:
        return cmd
    try:
        plat = _platform()
        if plat == "win" and hasattr(os, "startfile"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            return True
        subprocess.Popen(cmd, close_fds=(os.name != "nt"))
        return True
    except Exception:
        return False


def open_containing_folder(path: Path, dry_run: bool = False) -> bool | List[str]:
    cmd = build_reveal_command(path)
    if dry_run:
        return cmd
    try:
        subprocess.Popen(cmd, close_fds=(os.name != "nt"))
        return True
    except Exception:
        return False
