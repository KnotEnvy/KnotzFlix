# KnotzFLix – Agent Handoff Guide

This file orients the next developer team to resume work exactly where we left off. It summarizes scope, current status, how to run, what’s next, and key decisions.

## Project Snapshot
- Goal: Local‑first, offline Netflix‑style movie manager.
- Stack: Python 3.11+, PyQt6 (MVVM), SQLite + FTS5, ffmpeg/ffprobe.
- Repo layout: `ui/`, `domain/`, `infra/`, `tests/`.
- Status: Backend foundations, DB, scanning, parsing, hashing, basic posters cache, and minimal UI tabs (Library + Settings) are in. 24 tests passing.

## What’s Implemented
- Foundations
  - Data dirs (per‑OS) + `KNOTZFLIX_DATA_DIR` override for tests.
  - Rotating logs; JSON config persisted as `settings.json`.
  - Single‑instance lock (file lock). Focus IPC pending.
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
  - Poster generator (ffmpeg if available; otherwise 1×1 JPEG placeholder). Timestamp heuristic (20% into video) as a baseline.
- Playback & File Handling
  - Cross‑platform launch/default player commands and “open containing folder” (infra level).
- UI (early)
  - App shell with tabs: Library (poster grid) + Settings (roots list + Add/Rescan buttons).
  - Threaded scan with responsive progress bar; summary message; Library grid refresh.

## What’s Not Done (or Partial)
- Single‑instance focus (bring existing window to front): lock exists; IPC not wired.
- Posters heuristic: currently simple timestamp; luminance/edge heuristics still to implement.
- UI grid: basic QListView icon grid; needs virtualization sizing, keyboard focus ring polish, and type‑ahead.
- Instant search UI: FTS5 is in place; UI textbox/filter missing.
- Details page + shelves: not started.
- Locate Missing flow UI: DB relink helper exists; UI to guide users not done.
- Watchers (inotify/FSEvents/USN) and scoped rescans: not started.
- Packaging/first‑run wizard and QA hardening: not started.

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
- `infra/thumbnails.py`: poster generation (ffmpeg or placeholder), cache integration.
- `infra/library_service.py`: end‑to‑end scan → index → dupes/rename → probe → poster.
- `infra/playback.py`: external player launch + reveal in OS file explorer.
- `ui/app.py`: app entry + single‑instance guard.
- `ui/main_window.py`: tabs, folder chooser, rescan, progress.
- `ui/models/movie_list_model.py`: list model for movies with poster decoration.
- `ui/views/poster_grid.py`: grid view scaffold.

## Tests
- `tests/*` cover: paths/config/logging, DB CRUD/indexing, scanner/parser, fingerprinter, library service flows (dupes, rename, poster creation), ffprobe parsing, and playback commands.
- Run all: `python scripts/run_unittests.py`

## Immediate Next Steps (recommended)
1) Single‑instance focus IPC: small local TCP socket or named pipe; on second launch, send “focus” to running app; main window calls `raise()/activateWindow()`.
2) UI instant search: add a search box; query FTS5 and filter the model; target ≤100ms for 10k items.
3) Poster heuristics: brightness/edge based frame selection; add golden tests; keep deterministic seed.
4) Details view: show poster, title, year, runtime, res (badges), open/play buttons.
5) Empty state + toast errors: handle empty library and scan cancellation gracefully.
6) Watchers: add platform watchers + polling fallback; wire to per‑root rescans.

## Notes & Decisions
- Fingerprint hashing uses blake2b for now to avoid extra deps; easily swappable to BLAKE3 later.
- Posters are cached content‑addressed; reusing across rescans is in place.
- ffprobe/ffmpeg are optional; code paths gracefully fallback if not present.
- UI is structured for MVVM growth; current grid is a pragmatic list‑model starting point.

## Troubleshooting
- Tests failing due to path imports: ensure project root on `sys.path` or run via `scripts/run_unittests.py`.
- Windows `python -c` quoting in PowerShell: prefer using scripts to avoid quoting pitfalls.
- If ffmpeg is present but poster generation fails on synthetic inputs, the fallback placeholder ensures stability.

## PRD & Checklist
- Authoritative plan lives in `DOCS/PRD.md` and `DOCS/DevChecklist.md`.
- `DOCS/DevChecklist.md` is updated to current status with notes on partial items.

Happy hacking — and thank you for picking up KnotzFLix! 🚀
