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


def _is_safe_media_file(path: Path) -> bool:
    """Validate that file is a safe media file to open."""
    if not path.exists() or not path.is_file():
        return False
    
    # Check file extension against allowed media types
    safe_extensions = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
        '.mpg', '.mpeg', '.3gp', '.asf', '.rm', '.rmvb', '.vob', '.ts',
        '.m2ts', '.mts', '.divx', '.xvid', '.ogv', '.f4v', '.m2v'
    }
    
    if path.suffix.lower() not in safe_extensions:
        return False
    
    # Additional security: check file size is reasonable (not 0 and not > 50GB)
    try:
        size = path.stat().st_size
        if size == 0 or size > 50 * 1024 * 1024 * 1024:  # 50GB limit
            return False
    except (OSError, OverflowError):
        return False
    
    return True


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
    # SECURITY: Validate file before launching
    if not _is_safe_media_file(path):
        return False
    
    cmd = build_launch_command(path)
    if dry_run:
        return cmd
    try:
        # SECURITY FIX: Remove dangerous os.startfile usage, use subprocess consistently
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
