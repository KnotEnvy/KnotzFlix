import os
import shutil
import tempfile
import unittest
from pathlib import Path

from infra import config as cfg
from infra import logging_config, paths


class TestPathsConfigLogging(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="knotzflix_test_"))
        os.environ[paths.ENV_DATA_DIR] = str(self.tmpdir)

    def tearDown(self):
        try:
            shutil.rmtree(self.tmpdir, ignore_errors=True)
        finally:
            os.environ.pop(paths.ENV_DATA_DIR, None)

    def test_data_dirs_and_logging(self):
        d = paths.ensure_app_dirs()
        self.assertTrue(d["data"].exists())
        self.assertTrue(d["logs"].exists())

        logging_config.setup_logging()
        import logging

        logging.getLogger(__name__).info("hello world")
        log_path = paths.get_log_path()
        self.assertTrue(log_path.exists(), "log file should be created")
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("hello world", content)

    def test_config_save_load(self):
        c = cfg.AppConfig(library_roots=["/movies", "/usb/films"], concurrency=4)
        cfg.save_config(c)
        c2 = cfg.load_config()
        self.assertEqual(c.library_roots, c2.library_roots)
        self.assertEqual(c.concurrency, c2.concurrency)


if __name__ == "__main__":
    unittest.main()

