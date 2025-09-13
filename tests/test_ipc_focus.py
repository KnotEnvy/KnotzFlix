import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from infra import ipc_focus, paths


class TestIpcFocus(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="knotzflix_ipc_"))
        os.environ[paths.ENV_DATA_DIR] = str(self.tmpdir)

    def tearDown(self):
        os.environ.pop(paths.ENV_DATA_DIR, None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_focus_ping_roundtrip(self):
        called = {"v": 0}

        def cb():
            called["v"] += 1

        server = ipc_focus.start_server(cb)
        try:
            ok = ipc_focus.ping_existing()
            # Allow callback to be executed in server thread
            time.sleep(0.05)
            self.assertTrue(ok)
            self.assertGreaterEqual(called["v"], 1)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()

