# KnotzFLix – Agent Handoff Guide

This file orients the next developer team to resume work exactly where we left off. It summarizes scope, current status, how to run, what's next, and key decisions.

---

## Agent Update – 2025-09

This section captures recent changes and conventions to align future agents.

### Status Deltas
- Single-instance focus IPC: Implemented. Second launch pings the running app over localhost and brings the window to front.
- Instant search UI: Implemented in Library tab. Uses FTS5 when available with safe tokenization; falls back to LIKE.
- Posters heuristic: Improved. Prefers ffmpeg `thumbnail`; then scores deterministic candidate timestamps via `signalstats`/`edgedetect`; falls back to placeholder if needed.
- Details view: Implemented minimal dialog (poster, title/year, basic badges, Play/Open Folder).
- Shelves: Added tabs for Recently Added and By Folder (filters by selected root).
- Locate Missing flow: Context menu action to relink a missing file path.
- Watchers: Added lightweight polling fallback (QTimer) and optional native watchers via `watchdog` if installed.
- Toasts: Non-blocking toast widget added; used for Library actions.
- Validate Posters: One-click fixer in Settings; ffmpeg status indicator.

### Key Implementation Notes
- Threading/SQLite: Never share a `sqlite3.Connection` across threads. `ui.main_window.ScanWorker` opens a thread-local `Database` inside `run()`.
- FTS5 queries: Use `Database.search_titles(query)` which tokenizes input and builds a `token*` prefix query. Do not pass raw user strings to FTS5.
- Posters rendering: `PosterTileDelegate` draws a gradient using `QLinearGradient` with float coords. If a pixmap fails to load, a clear placeholder tile is rendered.
- Thumbnails pipeline: `infra/thumbnails.generate_poster` prefers `thumbnail` filter; dry-run returns a timestamp-based command to keep tests deterministic.
- Per-root rescans: Settings tab includes Remove Selected and Rescan Selected buttons. UI wires to the existing scan pipeline.

### Developer Shortcuts & UX
- Library grid shortcuts: `P` to Play, `R` to Reveal in file explorer. Double-click/Enter opens Details.
- Search debounce: 120 ms via QTimer. Tune as needed to meet ≤100 ms budget on large libraries.

### Tests & Validation
- Run tests: `python scripts/run_unittests.py` (31 tests passing at time of update).
- If you change thumbnails behavior, ensure `tests/test_thumbnails.py` expectations remain valid (dry-run returns a timestamp-based ffmpeg command containing `-ss` and `-vf`).

### Open Items (PRD/Checklist)
- Poster golden tests + deterministic seed for heuristic selection.
- Grid keyboard polish (PgUp/PgDn/Home/End selection by viewport rows/cols).
- Continue Watching shelf using `play_state` and progress badges.
- Real FS watchers (inotify/FSEvents/USN) with the polling fallback retained as a safety net.
- Packaging and first-run wizard.

### Gotchas
- JPEG warnings from Qt for some files are benign; ensure the delegate handles null pixmaps. Consider self-healing (swap to placeholder) if you see frequent decode failures.
- Keep DB migrations idempotent and FTS5 guarded; environments may lack FTS5.

## Project Snapshot
- Goal: Local‑first, offline Netflix‑style movie manager.
- Stack: Python 3.11+, PyQt6 (MVVM), SQLite + FTS5, ffmpeg/ffprobe.
- Repo layout: `ui/`, `domain/`, `infra/`, `tests/`.
- Status: Backend foundations, DB, scanning, parsing, hashing, posters cache, focus IPC, instant search, Library/Recently Added/By Folder/Continue Watching tabs, Details dialog, and Locate Missing are in. Tests passing.

## What’s Implemented
- Foundations
  - Data dirs (per‑OS) + `KNOTZFLIX_DATA_DIR` override for tests.
  - Rotating logs; JSON config persisted as `settings.json`.
  - Single‑instance lock (file lock) + focus IPC via localhost.
- Database
  - Migrations: v1 (core tables) + v2 (media metadata columns). FTS5 triggers keep index in sync.
  - CRUD + helpers (get by title/year, upsert media files, search, relink by path, images API).
- Scanner & Parser
  - Recursive scan, ignore rules (hidden, `Extras/`, `sample.*`), concurrency, progress callback.
  - Filename parser with 90%+ accuracy corpus test; `sort_title` rules.
- Media Probe & Hashing
  - `ffprobe` JSON parser and safe probe wrapper (optional if executable missing).
  - Partial fingerprint via blake2b (dependency‑free). Duplicate grouping and rename relink implemented.
- Posters/Cache
  - Content‑addressed cache with sharded paths; idempotent reuse.
  - Poster generator (ffmpeg if available; otherwise valid 1×1 PNG placeholder). Deterministic timestamp candidates + scoring.
- Playback & File Handling
  - Cross‑platform launch/default player commands and “open containing folder” (infra level).
- UI (early)
  - App shell with tabs: Library (poster grid with instant search), Recently Added, By Folder, Continue Watching, Settings.
  - Threaded scan with responsive progress bar; summary message; toasts for common actions; Library grids refresh.

## What’s Not Done (or Partial)
- Posters heuristic: advanced luminance/edge heuristics still to implement (currently thumbnail filter + timestamp fallback).
- UI grid polish: virtualization sizing, focus ring styling, and performance validation targets.
- Continue Watching: refine progress updates beyond initial seeding on Play.
- Real FS watchers: inotify/FSEvents/USN via native APIs; `watchdog` optional support added; polling fallback exists.
- Packaging/first‑run wizard and QA hardening.

## How to Run
- Tests (recommended): `python scripts/run_unittests.py`
- App (requires PyQt6):
  - Install: `pip install PyQt6` (inside your venv)
  - Run: `python scripts/run_app.py`
- Lint/Format (if tools available): `ruff check .` and `black --check .`

## Data & Paths
- Default user data dir depends on OS; override with `KNOTZFLIX_DATA_DIR` to use a temp directory.
- Files created: `db.sqlite3`, `settings.json`, `logs/knotzflix.log`, `cache/` (posters).

## Key Modules
- `infra/paths.py`: app data/log/cache paths.
- `infra/logging_config.py`: root logger with rotation.
- `infra/config.py`: `AppConfig` (roots, concurrency, ignore rules) + load/save.
- `infra/single_instance.py`: lock file guard.
- `infra/db.py`: migrations, CRUD, search, images, relink helpers.
- `infra/scanner.py`: recursive scanning, filters, concurrency.
- `infra/parser.py`: filename → title/year + `sort_title`.
- `infra/fingerprinter.py`: partial blake2b fingerprint.
- `infra/ffprobe.py`: safe probe + JSON parse to `MediaInfo`.
- `infra/cache.py`: content‑addressed cache utils.
- `infra/thumbnails.py`: poster generation (ffmpeg or placeholder), scoring, cache integration, ffmpeg status.
- `infra/library_service.py`: end‑to‑end scan → index → dupes/rename → probe → poster.
- `infra/playback.py`: external player launch + reveal in OS file explorer.
- `infra/ipc_focus.py`: localhost-based single-instance window focus IPC.
- `infra/watcher.py`: optional native watchers via watchdog; used with UI debounce.
- `ui/app.py`: app entry + single‑instance guard.
- `ui/main_window.py`: tabs, folder chooser, rescan, progress.
- `ui/models/movie_list_model.py`: list model for movies with poster decoration.
- `ui/views/poster_grid.py`: grid view with poster rendering, context actions.
- `ui/widgets/toast.py`: non-blocking toasts.

## Tests
- `tests/*` cover: paths/config/logging, DB CRUD/indexing, scanner/parser, fingerprinter, library service flows (dupes, rename, poster creation), ffprobe parsing, and playback commands.
- Run all: `python scripts/run_unittests.py`

## Immediate Next Steps (recommended)
1) Poster heuristics v2: implement brightness/edge scoring via ffmpeg signalstats/metadata on the deterministic candidate set; add golden tests for scoring fallbacks.
2) Grid performance + keyboard polish: verify ≤200ms first render, scroll smoothness, focus ring; refine PageUp/Down behavior by viewport rows/cols.
3) Continue Watching: wire progress updates on external playback handoff; refine progress badges.
4) Real FS watchers: add inotify/FSEvents/USN with opt-in and keep polling fallback.
5) First-run wizard + packaging: streamline onboarding and produce installers.

## Notes & Decisions
- Fingerprint hashing uses blake2b for now to avoid extra deps; easily swappable to BLAKE3 later.
- Posters are cached content‑addressed; reusing across rescans is in place.
- ffprobe/ffmpeg are optional; code paths gracefully fallback if not present.
- UI is structured for MVVM growth; current grid is a pragmatic list‑model starting point.

## Troubleshooting
- Tests failing due to path imports: ensure project root on `sys.path` or run via `scripts/run_unittests.py`.
- Windows `python -c` quoting in PowerShell: prefer using scripts to avoid quoting pitfalls.
- Posters: Check Settings for ffmpeg status; use “Validate Posters” to regenerate missing/placeholder posters; logs show failures.

## PRD & Checklist
- Authoritative plan lives in `DOCS/PRD.md` and `DOCS/DevChecklist.md`.
- `DOCS/DevChecklist.md` is updated to current status with notes on partial items.

Happy hacking — and thank you for picking up KnotzFLix! 🚀
