# KnotzFLix

KnotzFLix is a local-first, offline Netflix-style movie manager built with Python 3.11+, PyQt6, and SQLite (FTS5). It scans user-selected folders for movies, generates offline posters/thumbnails, and provides a fast, modern browsing experience. Playback is delegated to the system's default media player.

This repository follows the MVVM architecture with packages:
- `ui/` - views, viewmodels, widgets
- `domain/` - core models and business logic
- `infra/` - database, filesystem scanning, ffmpeg/ffprobe bridges, hashing
- `tests/` - pytest-based tests

## Development

- Python: 3.11+
- Lint: Ruff (`ruff check .`)
- Format: Black (`black .`)
- Tests: Pytest (`pytest`)

Optional dev dependencies are defined under `pyproject.toml` (`pip install .[dev]`).

Refer to DOCS/PRD.md and DOCS/DevChecklist.md for the authoritative plan.
