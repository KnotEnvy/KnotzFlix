# KnotzFLix

KnotzFLix is a local-first, offline Netflix-style movie manager for your own library. It scans folders, indexes titles into SQLite (FTS5), generates posters locally (with ffmpeg), and presents a fast, responsive PyQt6 UI.

Highlights
- Instant search (FTS5) with type-ahead filtering.
- Poster generation via ffmpeg with deterministic heuristics; offline placeholder fallback.
- Shelves: Library, Recently Added, By Folder, Continue Watching.
- Context menu actions: Play, Open Containing Folder, Details, Locate Missing, Mark Watched/Unwatched, Reset Progress.
- Non-blocking toasts for quick feedback; details dialog with badges.
- “Validate Posters” one-click fixer and ffmpeg status indicator in Settings.

Repository layout (MVVM-ish)
- `ui/` – views and widgets
- `domain/` – core models
- `infra/` – persistence, scanning, ffmpeg/ffprobe, hashing, thumbnails
- `tests/` – unit tests

Requirements
- Python 3.11+
- PyQt6 (UI)
- SQLite with FTS5 (bundled in Python’s stdlib sqlite on most platforms)
- ffmpeg (recommended for real posters; optional – placeholders used otherwise)

Quickstart
1) Create a venv and install dependencies:
   - `pip install PyQt6`
2) (Recommended) Install ffmpeg and ensure it’s on PATH:
   - Windows: download ffmpeg release and add the `bin` directory to PATH.
   - macOS: `brew install ffmpeg`
   - Linux: install from your distro’s package manager.
3) Run the app:
   - `python scripts/run_app.py`

Usage
- Add folders in Settings, then click “Rescan All”.
- Use the search box (top of Library) to filter instantly.
- Right-click a poster for actions (Play, Reveal, Details, Locate Missing, Mark watched/unwatched).
- Continue Watching appears automatically after playing (or seeded on Play if supported).
- Settings shows ffmpeg status and provides a “Validate Posters” button to regenerate missing/placeholder posters.

Keyboard
- P: Play; R: Reveal; W/U: Mark watched/unwatched
- Home/End/PageUp/PageDown: navigate in the grid
- Double-click/Enter: Details

Troubleshooting
- Posters blank/white: ensure ffmpeg is installed and on PATH; press “Validate Posters” in Settings.
- Data location: set `KNOTZFLIX_DATA_DIR` to override the default user data path.
- Logs: see `<data-dir>/logs/knotzflix.log` for errors.

Development
- Lint: `ruff check .`
- Format: `black .`
- Tests: `python scripts/run_unittests.py` (31 tests)

See `DOCS/PRD.md` and `DOCS/DevChecklist.md` for scope and status.
