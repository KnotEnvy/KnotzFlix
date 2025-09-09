from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DISPLAY_NAME = "KnotzFLix"
APP_SLUG = "knotzflix"
ENV_DATA_DIR = "KNOTZFLIX_DATA_DIR"


def get_data_dir() -> Path:
    """Return the OS-correct per-user data directory for the app.

    Honors `KNOTZFLIX_DATA_DIR` if set (useful for tests/portable runs).
    Windows: %LOCALAPPDATA%/KnotzFLix
    macOS: ~/Library/Application Support/KnotzFLix
    Linux: $XDG_DATA_HOME/knotzflix or ~/.local/share/knotzflix
    """
    override = os.getenv(ENV_DATA_DIR)
    if override:
        return Path(override).expanduser().resolve()

    home = Path.home()
    if sys.platform.startswith("win"):
        base = Path(os.getenv("LOCALAPPDATA", home / "AppData" / "Local"))
        return base / APP_DISPLAY_NAME
    elif sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_DISPLAY_NAME
    else:
        base = Path(os.getenv("XDG_DATA_HOME", home / ".local" / "share"))
        return base / APP_SLUG


def ensure_app_dirs() -> dict[str, Path]:
    """Ensure required app directories exist and return their paths.

    Returns keys: data, logs, cache
    """
    data_dir = get_data_dir()
    logs_dir = data_dir / "logs"
    cache_dir = data_dir / "cache"
    for p in (data_dir, logs_dir, cache_dir):
        p.mkdir(parents=True, exist_ok=True)
    return {"data": data_dir, "logs": logs_dir, "cache": cache_dir}


def get_log_path() -> Path:
    """Default log file path."""
    return ensure_app_dirs()["logs"] / f"{APP_SLUG}.log"


def get_db_path() -> Path:
    """Default SQLite database file path."""
    return ensure_app_dirs()["data"] / "db.sqlite3"

