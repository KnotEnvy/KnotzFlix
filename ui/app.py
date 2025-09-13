from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when running as a script
_project_root = str(Path(__file__).resolve().parents[1])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from infra import ipc_focus
from infra.logging_config import setup_logging
from infra.single_instance import SingleInstance, SingleInstanceError


def run() -> int:
    setup_logging()
    try:
        with SingleInstance():
            return _run_qt()
    except SingleInstanceError:
        # Notify existing instance to focus, if possible
        if ipc_focus.ping_existing():
            logging.getLogger(__name__).info("Signaled existing instance to focus window.")
            return 0
        logging.getLogger(__name__).warning("Another instance is already running (no focus signal).")
        return 0


def _run_qt() -> int:
    from PyQt6.QtWidgets import QApplication

    from ui.main_window import create_main_window

    app = QApplication([])
    win = create_main_window()
    # Start focus IPC server to bring window to front on subsequent launches
    try:
        server = ipc_focus.start_server(lambda: _focus_window(win))
        # Ensure server stops on app exit
        app.aboutToQuit.connect(lambda: server.stop())  # type: ignore[attr-defined]
    except Exception:
        pass
    win.show()
    return app.exec()


def _focus_window(win) -> None:
    try:
        win.raise_()
        win.activateWindow()
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(run())
