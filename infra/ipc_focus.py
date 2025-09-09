from __future__ import annotations

import socket
import socketserver
import threading
from pathlib import Path
from typing import Callable, Optional

from .paths import ensure_app_dirs


def _port_file() -> Path:
    return ensure_app_dirs()["data"] / "focus_port"


class _FocusTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, callback: Callable[[], None]):
        super().__init__(server_address, RequestHandlerClass)
        self.callback = callback


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            line = self.rfile.readline(64)
            if not line:
                return
            if line.strip().upper() == b"FOCUS":
                try:
                    self.server.callback()  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass


class FocusServer:
    def __init__(self, callback: Callable[[], None]):
        self._server: Optional[_FocusTCPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._callback = callback
        self._port: Optional[int] = None

    def start(self) -> None:
        # Bind to an ephemeral port on localhost
        srv = _FocusTCPServer(("127.0.0.1", 0), _Handler, self._callback)
        self._server = srv
        self._port = srv.server_address[1]
        # Write port to file for second instances
        pf = _port_file()
        pf.write_text(str(self._port), encoding="utf-8")

        t = threading.Thread(target=srv.serve_forever, name="focus-ipc", daemon=True)
        self._thread = t
        t.start()

    def stop(self) -> None:
        pf = _port_file()
        try:
            pf.unlink(missing_ok=True)
        except Exception:
            pass
        if self._server is not None:
            try:
                self._server.shutdown()
            finally:
                try:
                    self._server.server_close()
                except Exception:
                    pass
                self._server = None


def start_server(callback: Callable[[], None]) -> FocusServer:
    fs = FocusServer(callback)
    fs.start()
    return fs


def ping_existing() -> bool:
    pf = _port_file()
    try:
        port = int(pf.read_text(encoding="utf-8").strip())
    except Exception:
        return False
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0) as s:
            s.sendall(b"FOCUS\n")
            return True
    except OSError:
        return False

