from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class WatchHandle:
    def stop(self) -> None:
        pass


def start_watchers(roots: list[Path], on_change: Callable[[Path], None]) -> Optional[WatchHandle]:
    """Start platform-native file system watchers if available.

    Uses watchdog if installed. Falls back to None if unavailable; caller should
    retain any polling mechanism (e.g., QTimer).
    """
    try:
        from watchdog.events import FileSystemEventHandler  # type: ignore
        from watchdog.observers import Observer  # type: ignore
    except Exception:
        return None

    class Handler(FileSystemEventHandler):  # type: ignore[misc]
        def on_any_event(self, event):  # type: ignore[override]
            try:
                # event.src_path may be str; normalize to Path
                p = Path(getattr(event, "src_path", "."))
                # Find which root this path belongs to; notify with that root
                for r in roots:
                    try:
                        Path(p).resolve().as_posix().startswith(Path(r).resolve().as_posix())
                        on_change(Path(r))
                        break
                    except Exception:
                        continue
            except Exception:
                pass

    observer = Observer()
    h = Handler()
    for r in roots:
        try:
            observer.schedule(h, str(r), recursive=True)
        except Exception:
            continue
    observer.daemon = True
    observer.start()

    class _Handle(WatchHandle):
        def stop(self_nonlocal) -> None:
            try:
                observer.stop()
                observer.join(timeout=2)
            except Exception:
                pass

    return _Handle()

