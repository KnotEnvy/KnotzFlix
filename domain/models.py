from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Movie:
    id: Optional[int]
    canonical_title: str
    year: Optional[int] = None
    sort_title: Optional[str] = None
    edition: Optional[str] = None
    runtime_sec: Optional[int] = None
    source: Optional[str] = None


@dataclass
class MediaFile:
    id: Optional[int]
    movie_id: int
    path: str
    size_bytes: int
    mtime_ns: int
    inode: Optional[int] = None
    device: Optional[int] = None
    fingerprint: Optional[str] = None
    video_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    audio_channels: Optional[int] = None


@dataclass
class Image:
    id: Optional[int]
    movie_id: int
    kind: str  # poster/thumbnail
    path: str


@dataclass
class PlayState:
    movie_id: int
    position_sec: int
    watched: bool
