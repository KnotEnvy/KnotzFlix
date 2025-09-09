from pathlib import Path
import sys
import os
import time
import argparse
import signal
import subprocess
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from infra.single_instance import SingleInstance  # type: ignore
from infra import ipc_focus  # type: ignore
from ui.app import run  # type: ignore


def _read_pid_from_lock(lock_path: Path) -> Optional[int]:
    try:
        data = lock_path.read_text(encoding="utf-8").strip()
        return int(data) if data else None
    except Exception:
        return None


def _is_pid_running(pid: int) -> bool:
    if os.name == "nt":
        try:
            # Use tasklist filter to check for PID existence on Windows
            res = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            out = (res.stdout or "") + (res.stderr or "")
            return "No tasks are running which match" not in out
        except Exception:
            # Conservative fallback
            return False
    else:
        try:
            # On POSIX, signal 0 checks existence
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except Exception:
            return False


def _terminate_pid(pid: int, timeout: float = 3.0) -> bool:
    try:
        if os.name == "nt":
            # Forcefully terminate the process tree on Windows
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
            )
            return result.returncode == 0
        else:
            os.kill(pid, signal.SIGTERM)
            t0 = time.time()
            while time.time() - t0 < timeout:
                if not _is_pid_running(pid):
                    return True
                time.sleep(0.05)
            # escalate
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.1)
            return not _is_pid_running(pid)
    except Exception:
        return False


def _clean_stale_or_replace(replace: bool) -> None:
    lock_path = SingleInstance().lock_path
    if not lock_path.exists():
        return
    pid = _read_pid_from_lock(lock_path)
    if pid is None:
        # No PID recorded; assume stale and remove
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            pass
        return

    if _is_pid_running(pid):
        if replace:
            if _terminate_pid(pid):
                # Give the OS a moment to release resources, then remove lock
                time.sleep(0.1)
                try:
                    lock_path.unlink(missing_ok=True)
                except Exception:
                    pass
        else:
            # If another instance is running and we aren't replacing, try to ping it to focus and exit early
            if ipc_focus.ping_existing():
                print("Another KnotzFLix instance is running — focused the existing window.")
                raise SystemExit(0)
            else:
                print(
                    "Another KnotzFLix instance seems active. Rerun with --replace to terminate it, "
                    "or close the existing app first."
                )
                raise SystemExit(1)
    else:
        # Stale lock (PID not running) — remove
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run KnotzFLix UI")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Terminate an existing KnotzFLix instance if found and start a new one.",
    )
    args, unknown = parser.parse_known_args()

    # Pre-flight: clean stale lock or stop an existing instance if requested
    _clean_stale_or_replace(replace=args.replace)

    # Delegate to the UI app entrypoint
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
