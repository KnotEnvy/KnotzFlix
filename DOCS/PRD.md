# Aura — Product Requirements Document (MVP)

## 1. Overview
Aura is a cross-platform desktop app (Windows/macOS/Linux) that scans user-selected folders for movies, enriches them with **offline posters/thumbnails**, and presents a fast, modern, streaming-style UI. Playback is handled by the user’s **default external media player** (e.g., VLC) in MVP.

---

## 2. Goals & Non-Goals
**Goals (MVP)**
- Offline-first browsing and playback of locally stored movies.
- Lightning-fast scanning and **instant search** across titles.
- Netflix-like poster grid UI with detail views and “Play”.
- Stable packaging per OS; simple first-run setup.

**Non-Goals (MVP)**
- Online metadata scrapers (TMDb, OMDb).
- TV series/episodes support.
- Embedded video player.
- Auto-updates or network telemetry.
- File associations.

---

## 3. Key Metrics / SLAs
- Scan **2k movies** on SSD **≤ 30s** (incremental rescans ≤ 3s).
- First grid render after launch **≤ 200ms** on 5k items.
- Type-ahead search response **≤ 100ms** on 10k items.
- No UI freeze > 50ms under normal operations.

---

## 4. Target Users
- Movie collectors with multi-drive libraries (USB/NAS/internal).
- Platforms: Windows 11+, macOS 13+, Ubuntu 22.04+ (x86_64, ARM where feasible).

---

## 5. Core User Stories
1. Add Library Roots: select folders, Aura scans recursively.
2. See My Library: poster grid with smooth scrolling & keyboard navigation.
3. Search Instantly: type-ahead search results under 100ms.
4. View Details: large poster, title, year, file attributes (resolution, HDR).
5. Play Externally: play via default system media player.
6. Handle Missing Files: locate/relink or mark unavailable.
7. Mark Watched / Continue Watching: show Recently Added & Continue Watching shelves.

---

## 6. Scope & Features

### Library Scanning
- Recursive scan with ignore rules (`sample.*`, hidden/system, `Extras/`).
- Incremental updates (mtime, inode/device, partial hash).
- Concurrency with tunable worker count.

### Metadata (Offline)
- Filename parsing heuristics → title/year/edition.
- Optional ffprobe integration for codec/resolution/runtime.
- Poster/thumbnail generation from representative frame (ffmpeg).
- Manual “Fix Match” dialog for editing metadata.

### Search & Organization
- SQLite database with FTS5 search index.
- Shelves: Recently Added, Continue Watching, By Folder.
- Manual tags and collections (simple linking).

### Playback
- Launch via subprocess with robust path quoting.
- Missing-file detection & Locate dialog.
- Open-containing-folder action.

### UX & Accessibility
- Virtualized poster grid for large libraries.
- Keyboard navigation: arrows, Enter, Esc, Home/End, PgUp/PgDn.
- HiDPI/Scaling support; sharp assets at 125–200%.
- High-contrast mode, alt text, WCAG AA contrast.

### Reliability
- Incremental rescans; progress bar with no UI blocking.
- DB backups & migrations; rolling backups = 3.
- Config/import/export settings JSON.
- Reset library option.

### Packaging
- Windows: PyInstaller/Nuitka + NSIS/WiX.
- macOS: .app bundle + codesign/notarize.
- Linux: AppImage.
- Enforce single-instance execution.

---

## 7. Architecture

**Stack**
- Python 3.11+
- PyQt6 (MVVM pattern)
- SQLite + FTS5
- ffmpeg/ffprobe
- BLAKE3 for partial hashing

**Modules**
- `scanner`: walk FS, ignore rules
- `parser`: filename → metadata
- `fingerprinter`: hash + inode tracking
- `metadata`: ffprobe pipeline
- `thumbnails`: poster/thumbnail generation
- `index`: SQLite API + migrations
- `playback`: subprocess launch
- `watcher`: platform FS watchers (inotify/FSEvents/USN) + polling fallback
- `ui`: grid, details, wizard, shelves

---

## 8. Database Schema (condensed)

```sql
CREATE TABLE movie (
  id INTEGER PRIMARY KEY,
  canonical_title TEXT NOT NULL,
  year INTEGER,
  sort_title TEXT,
  edition TEXT,
  runtime_sec INTEGER,
  source TEXT,
  created_at TEXT, updated_at TEXT
);

CREATE TABLE file (
  id INTEGER PRIMARY KEY,
  movie_id INTEGER REFERENCES movie(id) ON DELETE CASCADE,
  path TEXT UNIQUE NOT NULL,
  size_bytes INTEGER,
  mtime_ns INTEGER,
  device_id TEXT, inode TEXT,
  hash_blake3_128 TEXT,
  codec TEXT, resolution TEXT, hdr TEXT, audio_channels INTEGER,
  created_at TEXT, updated_at TEXT
);

CREATE TABLE image (
  id INTEGER PRIMARY KEY,
  movie_id INTEGER REFERENCES movie(id) ON DELETE CASCADE,
  kind TEXT,
  path TEXT NOT NULL,
  width INTEGER, height INTEGER,
  src TEXT,
  UNIQUE(movie_id, kind)
);

CREATE VIRTUAL TABLE search_index USING fts5(
  title, alt_titles, year, tags, content=''
);

CREATE TABLE play_state (
  movie_id INTEGER PRIMARY KEY REFERENCES movie(id) ON DELETE CASCADE,
  last_position_sec INTEGER DEFAULT 0,
  completed INTEGER DEFAULT 0,
  last_played_at TEXT
);
```
---
## 9. System Requirements
- x86_64 CPU, 8 GB RAM (16 GB recommended).
- SSD recommended for large scans.
- Disk: <300 MB DB/cache (10k items, excludes posters).
- ffmpeg installed or bundled LGPL build.

---
## 10. Logging & Diagnostics
- Structured logs with rotation (10×5 MB).
- Diagnostics panel: show DB path, cache path, version, roots, worker counts.
- Crash dumps off by default; local only.

---
## 11. Licensing
- App under MIT (or Apache-2.0).
- Third-party notices shipped.
- ffmpeg bundled as LGPL build or user-installed system binary.

---
## 12. Out of Scope (MVP)
- Online metadata scrapers.
- Embedded player.
- Subtitles management.
- Auto-updates.
- File associations.
- TV series model.

---