from __future__ import annotations

import hashlib
from pathlib import Path

from .paths import ensure_app_dirs


def cache_root() -> Path:
    return ensure_app_dirs()["cache"]


def shard_path(key: str) -> Path:
    root = cache_root()
    return root / key[0:2] / key[2:4] / key


def ensure_parent_dirs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def make_key(*parts: str) -> str:
    h = hashlib.blake2s()
    for p in parts:
        h.update(p.encode("utf-8", errors="ignore"))
        h.update(b"|")
    return h.hexdigest()


def content_addressed_path(kind: str, fingerprint: str, variant: str, ext: str) -> Path:
    key = make_key(kind, fingerprint, variant)
    p = shard_path(key).with_suffix("." + ext.lstrip("."))
    ensure_parent_dirs(p)
    return p

