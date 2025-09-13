from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .paths import ensure_app_dirs

SETTINGS_FILE = "settings.json"


@dataclass
class AppConfig:
    """Application configuration persisted in user data directory.

    - library_roots: list of user-selected folder roots to scan
    - concurrency: default worker threads for scanner/probe tasks
    - ignore_rules: filename/directory patterns to skip during scanning
    """

    library_roots: list[str] = field(default_factory=list)
    # Folders whose contents are hidden from the main Library unless unlocked
    private_roots: list[str] = field(default_factory=list)
    # Blake2b hex digest of the private access code (optional)
    private_code_hash: str | None = None
    concurrency: int = max(os.cpu_count() or 2, 2)
    ignore_rules: list[str] = field(
        default_factory=lambda: [
            "sample.*",
            "*/Extras/*",
            "*/extras/*",
            "*/sample/*",
            "*/samples/*",
            "Thumbs.db",
            "desktop.ini",
        ]
    )


def _settings_path() -> Path:
    return ensure_app_dirs()["data"] / SETTINGS_FILE


def load_config() -> AppConfig:
    path = _settings_path()
    if not path.exists():
        return AppConfig()
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return AppConfig(**data)
    except Exception:
        # If file is corrupted, return defaults but keep file for inspection.
        return AppConfig()


def save_config(cfg: AppConfig) -> None:
    path = _settings_path()
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
