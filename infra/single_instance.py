from __future__ import annotations

import os
import time
from pathlib import Path

from .paths import ensure_app_dirs


class SingleInstanceError(RuntimeError):
    pass


class SingleInstance:
    """File-based single instance guard.

    Creates an exclusive lock file in the app data dir. If it already exists,
    consider another instance active and raise `SingleInstanceError`.

    Note: Stale lock detection is basic (mtime age check). Integrate IPC focus
    signaling with the UI later to meet the "focus first instance" criterion.
    """

    def __init__(self, lock_name: str = "app.lock", stale_after_sec: int = 24 * 3600) -> None:
        self.lock_path: Path = ensure_app_dirs()["data"] / lock_name
        self.fd: int | None = None
        self.stale_after_sec = stale_after_sec

    def acquire(self) -> None:
        # If file exists and is recent, assume active instance.
        if self.lock_path.exists():
            try:
                age = time.time() - self.lock_path.stat().st_mtime
            except OSError:
                age = 0
            if age < self.stale_after_sec:
                raise SingleInstanceError(f"Another instance is running: {self.lock_path}")
            else:
                # stale lock; remove
                try:
                    self.lock_path.unlink(missing_ok=True)
                except OSError:
                    pass
        flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
        try:
            self.fd = os.open(self.lock_path, flags, 0o644)
            os.write(self.fd, str(os.getpid()).encode("utf-8"))
        except FileExistsError:
            raise SingleInstanceError(f"Another instance is running: {self.lock_path}")

    def release(self) -> None:
        if self.fd is not None:
            try:
                os.close(self.fd)
            finally:
                self.fd = None
                try:
                    self.lock_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def __enter__(self) -> "SingleInstance":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

