import os
import shutil
import tempfile
import unittest
from pathlib import Path

from infra import paths, thumbnails


class TestThumbnails(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="knotzflix_thumbs_"))
        os.environ[paths.ENV_DATA_DIR] = str(self.tmpdir / "appdata")
        self.media = self.tmpdir / "dummy.mp4"
        # Create a dummy file (not a real video) to trigger fallback when ffmpeg tries to read
        self.media.write_bytes(b"not a real video")

    def tearDown(self):
        os.environ.pop(paths.ENV_DATA_DIR, None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_build_cmd_and_cache_path(self):
        out, cmd = thumbnails.generate_poster(self.media, file_fingerprint="f" * 64, duration_sec=120.0, dry_run=True)
        self.assertTrue(str(out).endswith(".jpg"))
        self.assertIsNotNone(cmd)
        self.assertIn("-ss", cmd)
        self.assertIn("-vf", cmd)

    def test_generate_placeholder_when_ffmpeg_fails(self):
        out, _ = thumbnails.generate_poster(self.media, file_fingerprint="e" * 64, duration_sec=50.0, dry_run=False)
        self.assertTrue(out.exists())
        # Second call should reuse without rewriting
        mtime_first = out.stat().st_mtime
        out2, _ = thumbnails.generate_poster(self.media, file_fingerprint="e" * 64, duration_sec=50.0, dry_run=False)
        self.assertEqual(out, out2)
        self.assertEqual(mtime_first, out2.stat().st_mtime)


if __name__ == "__main__":
    unittest.main()

