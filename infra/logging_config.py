from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .paths import ensure_app_dirs, get_log_path


def setup_logging(level: int = logging.INFO) -> None:
    """Configure app logging with rotation.

    - Rotating file log at 1MB, keep 3 backups
    - Stream handler to console at same level
    """
    ensure_app_dirs()
    log_path = get_log_path()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    existing = {(type(h), getattr(h, "baseFilename", None)) for h in root.handlers}
    if (type(file_handler), getattr(file_handler, "baseFilename", None)) not in existing:
        root.addHandler(file_handler)
    if (type(stream_handler), None) not in existing:
        root.addHandler(stream_handler)

