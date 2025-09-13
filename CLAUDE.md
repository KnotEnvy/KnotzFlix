# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KnotzFLix is a local-first, offline Netflix-style movie manager built with PyQt6 and SQLite. It scans folders for movies, generates posters locally using ffmpeg, and provides a fast, responsive UI for browsing and playing your personal movie library.

## Development Commands

### Running the Application
```bash
python scripts/run_app.py
```

### Testing
```bash
# Run all unit tests (31 tests)
python scripts/run_unittests.py

# Run with pytest (if dev dependencies installed)
pytest
```

### Code Quality
```bash
# Lint with ruff
ruff check .

# Format with black
black .

# Type checking with mypy (optional)
mypy .
```

## Architecture

The codebase follows an MVVM-like pattern with clear separation of concerns:

- **`ui/`** - PyQt6 views and widgets (main_window.py, poster_grid.py, details_dialog.py, toast.py)
- **`domain/`** - Core data models (Movie, MediaFile, Image, PlayState)
- **`infra/`** - Infrastructure layer including:
  - Database operations and SQLite with FTS5 search
  - File scanning and parsing
  - FFmpeg integration for poster generation
  - Playback launching
  - Configuration and logging

### Key Components

- **Scanner (`infra/scanner.py`)** - Recursively scans folders for media files with concurrency control
- **Parser (`infra/parser.py`)** - Extracts movie titles, years, and editions from filenames
- **Thumbnails (`infra/thumbnails.py`)** - Generates posters using ffmpeg with heuristic frame selection
- **Database (`infra/db.py`)** - SQLite operations with FTS5 full-text search indexing
- **Library Service (`infra/library_service.py`)** - Orchestrates scanning, parsing, and indexing

### Database Schema

Core entities:
- `movie` - Title, year, edition metadata
- `file` - File paths, sizes, hashes, codec info
- `image` - Generated posters and thumbnails
- `play_state` - Watch progress and completion status
- `search_index` - FTS5 virtual table for instant search

## Development Guidelines

### Dependencies
- Python 3.11+ required
- Core dependency: PyQt6
- Optional dev dependencies in pyproject.toml include pytest, black, ruff, mypy
- FFmpeg recommended for poster generation (falls back to placeholders)

### File Structure Patterns
- Follow the established module structure (`ui/`, `domain/`, `infra/`)
- Use type hints consistently (following existing patterns)
- Import PyQt6 components locally in functions when needed to avoid import overhead

### Testing
- Unit tests located in `tests/` directory
- Golden tests for poster generation determinism
- Test corpus for filename parsing accuracy

### Performance Considerations
- Virtualized poster grid for large libraries (10k+ items)
- SQLite FTS5 for sub-100ms search response
- Concurrent scanning with configurable worker counts
- Content-addressed caching for generated posters

### Configuration
- Settings stored in OS-appropriate user data directories
- Logging configured with rotation (see `infra/logging_config.py`)
- Single-instance enforcement via file locking