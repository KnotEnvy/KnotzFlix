from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Iterator, Optional

from domain.models import Movie, MediaFile, Image, PlayState
from .paths import get_db_path, ensure_app_dirs


CURRENT_SCHEMA_VERSION = 3


class Database:
    """SQLite database wrapper with migrations and simple CRUD."""

    def __init__(self, path: Optional[Path] = None) -> None:
        ensure_app_dirs()
        self.path = Path(path) if path else get_db_path()
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._fts5_supported = None

    @property
    def fts5_supported(self) -> bool:
        if self._fts5_supported is None:
            try:
                self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts_probe USING fts5(x)")
                self.conn.execute("DROP TABLE IF EXISTS _fts_probe")
                self._fts5_supported = True
            except sqlite3.OperationalError:
                self._fts5_supported = False
        return bool(self._fts5_supported)

    def close(self) -> None:
        self.conn.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def initialize(self) -> None:
        with self.tx() as cx:
            cx.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
            cur = cx.execute("SELECT version FROM schema_version LIMIT 1")
            row = cur.fetchone()
            version = int(row[0]) if row else 0
            if version < 1:
                self._apply_migration_1(cx)
                version = 1
                cx.execute("DELETE FROM schema_version")
                cx.execute("INSERT INTO schema_version (version) VALUES (1)")
            if version < 2:
                self._apply_migration_2(cx)
                version = 2
                cx.execute("UPDATE schema_version SET version = 2")
            if version < 3:
                self._apply_migration_3(cx)
                version = 3
                cx.execute("UPDATE schema_version SET version = 3")
            # Future migrations: bump until CURRENT_SCHEMA_VERSION

    def _apply_migration_1(self, cx: sqlite3.Connection) -> None:
        cx.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;

            CREATE TABLE movie (
              id INTEGER PRIMARY KEY,
              canonical_title TEXT NOT NULL,
              year INTEGER,
              sort_title TEXT,
              edition TEXT,
              runtime_sec INTEGER,
              source TEXT,
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE media_file (
              id INTEGER PRIMARY KEY,
              movie_id INTEGER NOT NULL REFERENCES movie(id) ON DELETE CASCADE,
              path TEXT NOT NULL UNIQUE,
              size_bytes INTEGER NOT NULL,
              mtime_ns INTEGER NOT NULL,
              inode INTEGER,
              device INTEGER,
              fingerprint TEXT
            );

            CREATE TABLE image (
              id INTEGER PRIMARY KEY,
              movie_id INTEGER NOT NULL REFERENCES movie(id) ON DELETE CASCADE,
              kind TEXT NOT NULL,
              path TEXT NOT NULL
            );

            CREATE TABLE play_state (
              movie_id INTEGER PRIMARY KEY REFERENCES movie(id) ON DELETE CASCADE,
              position_sec INTEGER NOT NULL DEFAULT 0,
              watched INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        if self.fts5_supported:
            cx.executescript(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS movie_fts
                USING fts5(canonical_title, content='movie', content_rowid='id');
                INSERT INTO movie_fts(rowid, canonical_title)
                SELECT id, canonical_title FROM movie;

                CREATE TRIGGER IF NOT EXISTS movie_ai AFTER INSERT ON movie BEGIN
                  INSERT INTO movie_fts(rowid, canonical_title) VALUES (new.id, new.canonical_title);
                END;
                CREATE TRIGGER IF NOT EXISTS movie_ad AFTER DELETE ON movie BEGIN
                  INSERT INTO movie_fts(movie_fts, rowid, canonical_title) VALUES('delete', old.id, old.canonical_title);
                END;
                CREATE TRIGGER IF NOT EXISTS movie_au AFTER UPDATE OF canonical_title ON movie BEGIN
                  INSERT INTO movie_fts(movie_fts, rowid, canonical_title) VALUES('delete', old.id, old.canonical_title);
                  INSERT INTO movie_fts(rowid, canonical_title) VALUES (new.id, new.canonical_title);
                END;
                """
            )

    def _apply_migration_2(self, cx: sqlite3.Connection) -> None:
        # Add media metadata columns to media_file
        cx.executescript(
            """
            ALTER TABLE media_file ADD COLUMN video_codec TEXT;
            ALTER TABLE media_file ADD COLUMN width INTEGER;
            ALTER TABLE media_file ADD COLUMN height INTEGER;
            ALTER TABLE media_file ADD COLUMN audio_channels INTEGER;
            """
        )

    def _apply_migration_3(self, cx: sqlite3.Connection) -> None:
        # Extend image table with optional width/height and src, and add a UNIQUE(movie_id, kind) if not present
        # Add columns only if missing (guards re-entrancy/partial migrations)
        try:
            cols = {row[1] for row in cx.execute("PRAGMA table_info(image)")}
        except Exception:
            cols = set()
        if "width" not in cols:
            try:
                cx.execute("ALTER TABLE image ADD COLUMN width INTEGER")
            except sqlite3.OperationalError:
                pass
        if "height" not in cols:
            try:
                cx.execute("ALTER TABLE image ADD COLUMN height INTEGER")
            except sqlite3.OperationalError:
                pass
        if "src" not in cols:
            try:
                cx.execute("ALTER TABLE image ADD COLUMN src TEXT")
            except sqlite3.OperationalError:
                pass
        # Deduplicate any existing rows so a unique index can be created safely.
        # Keep the lowest id per (movie_id, kind), remove others.
        try:
            cx.execute(
                "DELETE FROM image WHERE id NOT IN (SELECT MIN(id) FROM image GROUP BY movie_id, kind)"
            )
        except Exception:
            pass
        # Attempt to add a uniqueness constraint via an index (SQLite cannot easily add UNIQUE to existing table)
        cx.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_image_unique ON image(movie_id, kind)")

    # CRUD operations
    def add_movie(self, m: Movie) -> int:
        with self.tx() as cx:
            cur = cx.execute(
                "INSERT INTO movie (canonical_title, year, sort_title, edition, runtime_sec, source)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (m.canonical_title, m.year, m.sort_title, m.edition, m.runtime_sec, m.source),
            )
            movie_id = int(cur.lastrowid)
            if self.fts5_supported:
                cx.execute(
                    "INSERT INTO movie_fts(rowid, canonical_title) VALUES(?, ?)",
                    (movie_id, m.canonical_title),
                )
            return movie_id

    def get_movie(self, movie_id: int) -> Optional[Movie]:
        cur = self.conn.execute(
            "SELECT id, canonical_title, year, sort_title, edition, runtime_sec, source FROM movie WHERE id=?",
            (movie_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Movie(
            id=row["id"],
            canonical_title=row["canonical_title"],
            year=row["year"],
            sort_title=row["sort_title"],
            edition=row["edition"],
            runtime_sec=row["runtime_sec"],
            source=row["source"],
        )

    def get_movie_by_title_year(self, title: str, year: Optional[int]) -> Optional[Movie]:
        if year is None:
            cur = self.conn.execute(
                "SELECT id, canonical_title, year, sort_title, edition, runtime_sec, source FROM movie WHERE canonical_title=? AND year IS NULL",
                (title,),
            )
        else:
            cur = self.conn.execute(
                "SELECT id, canonical_title, year, sort_title, edition, runtime_sec, source FROM movie WHERE canonical_title=? AND year=?",
                (title, year),
            )
        row = cur.fetchone()
        if not row:
            return None
        return Movie(
            id=row["id"],
            canonical_title=row["canonical_title"],
            year=row["year"],
            sort_title=row["sort_title"],
            edition=row["edition"],
            runtime_sec=row["runtime_sec"],
            source=row["source"],
        )

    def update_movie_title(self, movie_id: int, title: str) -> None:
        with self.tx() as cx:
            cx.execute("UPDATE movie SET canonical_title=?, updated_at=datetime('now') WHERE id=?", (title, movie_id))
            # FTS5 triggers keep the index in sync when enabled

    def add_media_file(self, f: MediaFile) -> int:
        with self.tx() as cx:
            cur = cx.execute(
                "INSERT INTO media_file (movie_id, path, size_bytes, mtime_ns, inode, device, fingerprint)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f.movie_id, f.path, f.size_bytes, f.mtime_ns, f.inode, f.device, f.fingerprint),
            )
            return int(cur.lastrowid)

    def get_media_file_by_path(self, path: str) -> Optional[MediaFile]:
        cur = self.conn.execute(
            "SELECT id, movie_id, path, size_bytes, mtime_ns, inode, device, fingerprint, video_codec, width, height, audio_channels FROM media_file WHERE path=?",
            (path,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return MediaFile(
            id=row["id"],
            movie_id=row["movie_id"],
            path=row["path"],
            size_bytes=row["size_bytes"],
            mtime_ns=row["mtime_ns"],
            inode=row["inode"],
            device=row["device"],
            fingerprint=row["fingerprint"],
            video_codec=row["video_codec"],
            width=row["width"],
            height=row["height"],
            audio_channels=row["audio_channels"],
        )

    def get_media_files_by_fingerprint(self, fingerprint: str) -> list[MediaFile]:
        cur = self.conn.execute(
            "SELECT id, movie_id, path, size_bytes, mtime_ns, inode, device, fingerprint, video_codec, width, height, audio_channels FROM media_file WHERE fingerprint=?",
            (fingerprint,),
        )
        res = []
        for row in cur.fetchall():
            res.append(
                MediaFile(
                    id=row["id"],
                    movie_id=row["movie_id"],
                    path=row["path"],
                    size_bytes=row["size_bytes"],
                    mtime_ns=row["mtime_ns"],
                    inode=row["inode"],
                    device=row["device"],
                    fingerprint=row["fingerprint"],
                    video_codec=row["video_codec"],
                    width=row["width"],
                    height=row["height"],
                    audio_channels=row["audio_channels"],
                )
            )
        return res

    def upsert_media_file(self, f: MediaFile) -> int:
        existing = self.get_media_file_by_path(f.path)
        if existing:
            with self.tx() as cx:
                cx.execute(
                    "UPDATE media_file SET movie_id=?, size_bytes=?, mtime_ns=?, inode=?, device=?, fingerprint=? WHERE id=?",
                    (
                        f.movie_id,
                        f.size_bytes,
                        f.mtime_ns,
                        f.inode,
                        f.device,
                        f.fingerprint,
                        existing.id,
                    ),
                )
                return int(existing.id)  # type: ignore[arg-type]
        return self.add_media_file(f)

    def update_media_file_path_and_stats(
        self,
        file_id: int,
        *,
        new_path: str,
        size_bytes: int,
        mtime_ns: int,
        inode: Optional[int],
        device: Optional[int],
        fingerprint: Optional[str],
    ) -> None:
        with self.tx() as cx:
            cx.execute(
                "UPDATE media_file SET path=?, size_bytes=?, mtime_ns=?, inode=?, device=?, fingerprint=? WHERE id=?",
                (new_path, size_bytes, mtime_ns, inode, device, fingerprint, file_id),
            )

    def update_media_file_metadata(
        self,
        file_id: int,
        *,
        video_codec: Optional[str],
        width: Optional[int],
        height: Optional[int],
        audio_channels: Optional[int],
    ) -> None:
        with self.tx() as cx:
            cx.execute(
                "UPDATE media_file SET video_codec=?, width=?, height=?, audio_channels=? WHERE id=?",
                (video_codec, width, height, audio_channels, file_id),
            )

    def set_movie_runtime(self, movie_id: int, runtime_sec: Optional[int]) -> None:
        with self.tx() as cx:
            cx.execute(
                "UPDATE movie SET runtime_sec=?, updated_at=datetime('now') WHERE id=?",
                (runtime_sec, movie_id),
            )

    def relink_media_file_by_path(self, old_path: str, new_path: str) -> bool:
        mf = self.get_media_file_by_path(old_path)
        if not mf:
            return False
        self.update_media_file_path_and_stats(
            file_id=int(mf.id),  # type: ignore[arg-type]
            new_path=new_path,
            size_bytes=mf.size_bytes,
            mtime_ns=mf.mtime_ns,
            inode=mf.inode,
            device=mf.device,
            fingerprint=mf.fingerprint,
        )
        return True

    def add_image(self, img: Image) -> int:
        with self.tx() as cx:
            cur = cx.execute(
                "INSERT OR REPLACE INTO image (id, movie_id, kind, path, width, height, src) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (img.id, img.movie_id, img.kind, img.path, img.width, img.height, img.src),
            )
            return int(cur.lastrowid)

    def get_images_for_movie(self, movie_id: int, kind: str | None = None) -> list[Image]:
        if kind is None:
            cur = self.conn.execute(
                "SELECT id, movie_id, kind, path, width, height, src FROM image WHERE movie_id=?",
                (movie_id,),
            )
        else:
            cur = self.conn.execute(
                "SELECT id, movie_id, kind, path, width, height, src FROM image WHERE movie_id=? AND kind=?",
                (movie_id, kind),
            )
        res: list[Image] = []
        for row in cur.fetchall():
            res.append(Image(id=row["id"], movie_id=row["movie_id"], kind=row["kind"], path=row["path"], width=row["width"], height=row["height"], src=row["src"]))
        return res

    def get_media_files_for_movie(self, movie_id: int) -> list[MediaFile]:
        cur = self.conn.execute(
            "SELECT id, movie_id, path, size_bytes, mtime_ns, inode, device, fingerprint, video_codec, width, height, audio_channels FROM media_file WHERE movie_id=? ORDER BY id",
            (movie_id,),
        )
        res: list[MediaFile] = []
        for row in cur.fetchall():
            res.append(
                MediaFile(
                    id=row["id"],
                    movie_id=row["movie_id"],
                    path=row["path"],
                    size_bytes=row["size_bytes"],
                    mtime_ns=row["mtime_ns"],
                    inode=row["inode"],
                    device=row["device"],
                    fingerprint=row["fingerprint"],
                    video_codec=row["video_codec"],
                    width=row["width"],
                    height=row["height"],
                    audio_channels=row["audio_channels"],
                )
            )
        return res

    def get_movie_ids_by_path_prefix(self, prefix: str) -> list[int]:
        p = prefix.replace("\\", "/")
        cur = self.conn.execute(
            "SELECT DISTINCT movie_id FROM media_file WHERE REPLACE(path, '\\', '/') LIKE ?",
            (p.rstrip("/") + "/%",),
        )
        return [int(r[0]) for r in cur.fetchall()]

    def get_all_movie_ids(self) -> list[int]:
        cur = self.conn.execute("SELECT id FROM movie ORDER BY id")
        return [int(r[0]) for r in cur.fetchall()]

    # Play state helpers
    def get_play_state(self, movie_id: int) -> Optional[PlayState]:
        cur = self.conn.execute(
            "SELECT position_sec, watched FROM play_state WHERE movie_id=?",
            (movie_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return PlayState(movie_id=movie_id, position_sec=row[0], watched=bool(row[1]))

    def set_watched(self, movie_id: int, watched: bool) -> None:
        st = self.get_play_state(movie_id)
        pos = st.position_sec if st else 0
        self.set_play_state(PlayState(movie_id=movie_id, position_sec=pos, watched=watched))

    def reset_progress(self, movie_id: int) -> None:
        self.set_play_state(PlayState(movie_id=movie_id, position_sec=0, watched=False))

    def get_continue_watching_ids(self) -> list[int]:
        cur = self.conn.execute(
            "SELECT movie_id FROM play_state WHERE watched=0 AND position_sec>0 ORDER BY position_sec DESC"
        )
        return [int(r[0]) for r in cur.fetchall()]

    def set_play_state(self, st: PlayState) -> None:
        with self.tx() as cx:
            cx.execute(
                "INSERT INTO play_state (movie_id, position_sec, watched) VALUES (?, ?, ?)"
                " ON CONFLICT(movie_id) DO UPDATE SET position_sec=excluded.position_sec, watched=excluded.watched",
                (st.movie_id, st.position_sec, int(st.watched)),
            )

    def search_titles(self, query: str) -> list[int]:
        q = (query or "").strip()
        if not q:
            return []
        if not self.fts5_supported:
            cur = self.conn.execute(
                "SELECT id FROM movie WHERE canonical_title LIKE ?",
                (f"%{q}%",),
            )
            return [r[0] for r in cur.fetchall()]
        # Sanitize for FTS5: split into alnum tokens and do prefix match per token
        import re
        tokens = re.findall(r"[A-Za-z0-9]+", q)
        if not tokens:
            return []
        match = " ".join(t + "*" for t in tokens)
        cur = self.conn.execute(
            "SELECT rowid FROM movie_fts WHERE movie_fts MATCH ?",
            (match,),
        )
        return [r[0] for r in cur.fetchall()]
