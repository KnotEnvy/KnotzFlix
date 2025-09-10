from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".m4v", ".wmv"}


@dataclass
class ScanItem:
    path: Path
    size_bytes: int
    mtime_ns: int


def _is_hidden(name: str) -> bool:
    return name.startswith(".")


def iter_video_files(roots: Iterable[Path], ignore_rules: Iterable[str]) -> Iterator[Path]:
    rules = list(ignore_rules)
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # prune hidden and Extras/Sample directories
            dirnames[:] = [
                d for d in dirnames if not _is_hidden(d) and d.lower() not in {"extras", "sample", "samples"}
            ]

            for fn in filenames:
                if _is_hidden(fn):
                    continue
                lowered = fn.lower()
                if any(pat.lower() in lowered for pat in ("thumbs.db", "desktop.ini")):
                    continue
                # simple sample.* filter (files named sample.*)
                if lowered.startswith("sample."):
                    continue
                p = Path(dirpath) / fn
                if p.suffix.lower() in VIDEO_EXTS:
                    # path-based ignore rules (simple contains match)
                    p_str = str(p).replace("\\", "/").lower()
                    if any(rule.lower() in p_str for rule in rules):
                        continue
                    yield p


def scan(roots: Iterable[Path], ignore_rules: Iterable[str], workers: int = 8) -> list[ScanItem]:
    files = list(iter_video_files(roots, ignore_rules))
    def stat_path(p: Path) -> ScanItem:
        st = p.stat()
        return ScanItem(path=p, size_bytes=st.st_size, mtime_ns=st.st_mtime_ns)

    if workers <= 1:
        return [stat_path(p) for p in files]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(stat_path, files))
