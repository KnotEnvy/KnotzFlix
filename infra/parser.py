from __future__ import annotations

import re
from typing import Optional, Tuple

YEAR_RE = re.compile(r"(?<!\d)((19|20)\d{2})(?!\d)")


def parse_filename(name: str) -> Tuple[str, Optional[int]]:
    """Parse a movie filename into (title, year).

    Supports patterns like:
    - Title (2021).mkv
    - Title.2021.1080p.mkv
    - Title - 2021 [UHD].mkv
    """
    stem = name
    # strip extension
    if "." in name:
        stem = name.rsplit(".", 1)[0]
    # replace separators with spaces
    cleaned = re.sub(r"[._-]+", " ", stem).strip()
    year = None
    m = YEAR_RE.search(cleaned)
    if m:
        year = int(m.group(1))
        title = cleaned[: m.start()].strip()
    else:
        title = cleaned
    # remove trailing bracketed expressions and stray opening braces
    title = re.sub(r"\s*\[(.*?)\]$", "", title).strip()
    title = re.sub(r"\s*\((.*?)\)$", "", title).strip()
    title = title.rstrip(" ([{")
    # Title-case except known uppercase tokens remain
    if title:
        title = " ".join(w.capitalize() if not w.isupper() else w for w in title.split())
    return title, year


def make_sort_title(title: str) -> str:
    t = title.strip()
    lowered = t.lower()
    for prefix in ("the ", "a ", "an "):
        if lowered.startswith(prefix):
            return t[len(prefix) :].strip()
    return t
