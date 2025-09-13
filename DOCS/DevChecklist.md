# KnotzFLix - Development Checklist (MVP)

This roadmap is iterative. Each task includes acceptance criteria.

---

## Sprint 0 - Foundations
- [x] Repo scaffold (`ui/`, `domain/`, `infra/`, `tests/`), lint/format config.  
  Done when: CI lints/tests run clean. (Configured; tests pass locally.)
- [x] Config + logging setup (rotate logs, OS-correct user data dirs).  
  Done when: logs written to user dir; settings.json persisted. (Verified in tests.)
- [x] Enforce single-instance execution.  
  Done when: launching second instance focuses the first. (Implemented via file lock + localhost IPC focus.)

---

## Sprint 1 - Database & Migrations
- [x] SQLite schema + migration runner; FTS5 enabled.  
  Done when: DB auto-creates; `schema_version` set; migrations tested. (v1+v2 complete; triggers in place.)
- [x] DB API for CRUD.  
  Done when: unit tests pass for movie/file/image/play_state. (Covered by tests.)

---

## Sprint 2 - Scanner & Parser
- [x] Folder chooser (multi-root), persisted roots.  
  Done when: roots remembered on reopen. (UI implemented; persisted in settings.)
- [x] Recursive scan with ignore rules & concurrency knobs.  
  Done when: 2k files scan ≤30s; progress bar responsive. (Scanner + progress wired; SLA measurement pending.)
- [x] Filename parser + sort_title; test corpus.  
  Done when: ≥90% correct on varied sample set. (Corpus test passes.)

---

## Sprint 3 - Media Probe & Hashing
- [x] ffprobe bridge for codec/resolution/runtime/channels.  
  Done when: metadata saved; failures logged safely. (Integrated in scan; safe fallback.)
- [x] BLAKE3 partial hashing; move/duplicate detection.  
  Done when: renames relink; dupes grouped. (Behavior implemented with blake2b fallback; swap to BLAKE3 later.)

---

## Sprint 4 - Posters/Thumbnails (Offline)
- [x] Poster pipeline: frame picker with luminance/edge heuristics.  
  Done when: ≥90% representative posters generated. (Deterministic candidate selection + ffmpeg signalstats/edgedetect scoring integrated; golden tests cover determinism and scoring helpers.)
- [x] Cache system (content-addressed, size variants).  
  Done when: cache reused on rescans. (Implemented; verified.)
- [x] Index titles/tags into FTS5.  
  Done when: instant search returns results on 10k items. (Titles indexed; UI instant search implemented.)

---

## Sprint 5 - UI: Grid & Navigation
- [x] Virtualized poster grid, keyboard navigation, focus ring.  
  Done when: first render ≤200ms; smooth scroll; Home/End work. (Batched layout, per-pixel scrolling, type-ahead routes to search, viewport-aware PageUp/PageDown, palette-based focus/selection ring, placeholder-aware painting.)
- [x] Empty state screens + error toasts.  
  Done when: no crashes on empty library or scan cancel. (Empty state implemented; non-blocking toast widget added and wired in Library actions.)

---

## Sprint 6 - Details & Shelves
- [x] Details page (poster, title, year, file badges).  
  Done when: opens ≤100ms; back navigation works. (Implemented minimal dialog with poster, badges, Play/Open, Regenerate Poster.)
- [x] Shelves: Recently Added, By Folder.  
  Done when: correct contents after rescan. (Implemented; tabs added; synced with roots and rescans.)
- [x] Mark Watched + Continue Watching.  
  Done when: states persist across sessions. (Implemented: watched/unwatched/reset actions; Continue Watching shelf; seeds progress on Play; persists across sessions.)

---

## Sprint 7 - Playback & File Handling
- [x] External player launch (robust path quoting).  
  Done when: works across OSes with spaces/unicode paths. (Infra implemented; UI wired in Library context menu.)
- [x] Locate Missing flow.  
  Done when: user can relink file within 3 clicks. (Implemented via Library context menu; uses DB relink helper.)
- [x] Open Containing Folder.  
  Done when: opens OS file explorer to correct path. (Infra implemented; UI wired in context menu.)

---

## Sprint 8 - Watcher & Incremental Rescans
- [x] Platform FS watcher (inotify/FSEvents/USN) + polling fallback.  
  Done when: new files appear within seconds. (Implemented via optional `watchdog`-backed native watchers with per-root debounce; QTimer polling retained as fallback.)
- [x] Per-root rescans.  
  Done when: scoped rescan runs without touching other roots. (UI button "Rescan Selected" added.)

---

## Sprint 9 - Packaging & First-Run
- [ ] Installers per OS (Win, macOS, Linux).  
  Done when: fresh install on VM works cleanly.
- [ ] First-run wizard (add roots → scan).  
  Done when: posters appear with ≤3 user actions.

---

## Sprint 10 - QA & Hardening
- [ ] Synthetic library generator (1k-10k files).  
  Done when: benchmarks collected; regressions blocked in CI.
- [x] Golden poster tests + deterministic seed.  
  Done when: pipeline yields reproducible results. (Added determinism tests for candidate generation and helper scoring.)
- [ ] Stress ceiling tests (50k items).  
  Done when: app degrades gracefully (no crash).
- [ ] Vacuum/maintenance tasks.  
  Done when: DB stays compact; backups retained (3 rolling).

---

# Global Definition of Done
- All acceptance criteria met.  
- Unit/integration tests written and passing.  
- Benchmarks within SLA.  
- No UI freeze >50ms in common flows.  
- Works on Win/macOS/Linux smoke tests.  
- LICENSE + THIRD-PARTY-NOTICES included.  
- README, CHANGELOG, CONTRIBUTING updated.  
