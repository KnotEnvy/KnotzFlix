from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from domain.models import MediaFile, Movie, Image
from . import scanner, parser, fingerprinter
from .db import Database
from . import thumbnails


@dataclass
class ScanSummary:
    total_files: int
    new_movies: int
    new_files: int
    duplicates: int


ProgressCallback = Callable[[int, int], None]  # processed, total


def scan_and_index(
    db: Database,
    roots: Iterable[Path],
    ignore_rules: Iterable[str],
    concurrency: int = 8,
    do_fingerprint: bool = True,
    progress: Optional[ProgressCallback] = None,
    probe_func: Optional[Callable[[Path], object]] = None,
) -> ScanSummary:
    items = scanner.scan(roots, ignore_rules, workers=concurrency)
    total = len(items)
    new_movies = 0
    new_files = 0
    duplicates = 0

    # Lazy import to avoid hard dependency in environments without ffprobe
    if probe_func is None:
        try:
            from .ffprobe import probe as default_probe  # type: ignore
            probe_func = default_probe
        except Exception:
            probe_func = None

    for idx, it in enumerate(items, start=1):
        title, year = parser.parse_filename(it.path.name)
        sort_title = parser.make_sort_title(title)

        fp: Optional[str] = None
        if do_fingerprint:
            try:
                fp = fingerprinter.fingerprint_partial(it.path)
            except Exception:
                fp = None

        # Resolve movie ID: prefer fingerprint match; else title+year; else create
        movie_id: Optional[int] = None
        existing_files = db.get_media_files_by_fingerprint(fp) if fp else []
        if existing_files:
            movie_id = existing_files[0].movie_id
            # Detect rename: if exactly one existing file and path differs, update path
            if (
                len(existing_files) == 1
                and existing_files[0].path != str(it.path)
                and not Path(existing_files[0].path).exists()
            ):
                db.update_media_file_path_and_stats(
                    file_id=int(existing_files[0].id),  # type: ignore[arg-type]
                    new_path=str(it.path),
                    size_bytes=it.size_bytes,
                    mtime_ns=it.mtime_ns,
                    inode=None,
                    device=None,
                    fingerprint=fp,
                )
            else:
                duplicates += 1

        if movie_id is None:
            existing_movie = db.get_movie_by_title_year(title, year)
            if existing_movie:
                movie_id = existing_movie.id
            else:
                movie_id = db.add_movie(
                    Movie(
                        id=None,
                        canonical_title=title,
                        year=year,
                        sort_title=sort_title,
                        edition=None,
                        runtime_sec=None,
                        source="scan",
                    )
                )
                new_movies += 1

        # Upsert media file row
        mf = MediaFile(
            id=None,
            movie_id=int(movie_id),  # type: ignore[arg-type]
            path=str(it.path),
            size_bytes=it.size_bytes,
            mtime_ns=it.mtime_ns,
            inode=None,
            device=None,
            fingerprint=fp,
        )
        before = db.get_media_file_by_path(mf.path)
        db.upsert_media_file(mf)
        after = db.get_media_file_by_path(mf.path)
        if before is None and after is not None:
            new_files += 1

        # Probe media info and persist
        duration_for_poster: Optional[float] = None
        if probe_func is not None and after is not None:
            try:
                info = probe_func(Path(after.path))  # type: ignore[arg-type]
            except Exception:
                info = None
            if info is not None:
                # duck-typed expected attributes
                video_codec = getattr(info, "codec_name", None)
                width = getattr(info, "width", None)
                height = getattr(info, "height", None)
                channels = getattr(info, "channels", None)
                duration_sec = getattr(info, "duration_sec", None)
                db.update_media_file_metadata(
                    file_id=int(after.id),  # type: ignore[arg-type]
                    video_codec=video_codec,
                    width=width,
                    height=height,
                    audio_channels=channels,
                )
                # Update movie runtime if not set
                m = db.get_movie(int(movie_id))
                if m and (m.runtime_sec is None) and duration_sec is not None:
                    db.set_movie_runtime(int(movie_id), int(duration_sec))
                duration_for_poster = duration_sec

        # Optionally generate poster and record in DB (placeholder if ffmpeg unavailable)
        if do_fingerprint and fp and after is not None:
            try:
                out_path, _ = thumbnails.generate_poster(
                    Path(after.path),
                    file_fingerprint=fp,
                    duration_sec=duration_for_poster,
                    dry_run=False,
                )
                # add image row if not present
                imgs = db.get_images_for_movie(int(movie_id), kind="poster")
                if not any(Path(img.path) == out_path for img in imgs):
                    # src hints at creation method
                    src = "ffmpeg" if out_path.exists() else "placeholder"
                    db.add_image(Image(id=None, movie_id=int(movie_id), kind="poster", path=str(out_path), src=src))
            except Exception:
                pass

        if progress:
            progress(idx, total)

    return ScanSummary(total_files=total, new_movies=new_movies, new_files=new_files, duplicates=duplicates)
