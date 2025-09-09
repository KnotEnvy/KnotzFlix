import os
import shutil
import tempfile
import unittest
from pathlib import Path

from infra import library_service
from infra import paths
from infra.db import Database
from infra import db as dbmod


class TestLibraryService(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="knotzflix_lib_"))
        # Redirect app data dir
        os.environ[paths.ENV_DATA_DIR] = str(self.tmpdir / "appdata")

        # Create a small library
        self.lib = self.tmpdir / "lib"
        self.lib.mkdir()
        # two identical files (duplicate content)
        data = (b"A" * 1024) + (b"B" * 1024) + (b"C" * 1024)
        (self.lib / "MovieA.2020.mkv").write_bytes(data)
        (self.lib / "MovieA.2020.copy.mkv").write_bytes(data)
        # a different file
        (self.lib / "MovieB.2021.mkv").write_bytes(b"X" * 4096)

        self.db = Database()
        self.db.initialize()

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass
        os.environ.pop(paths.ENV_DATA_DIR, None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_scan_and_index_with_fingerprint(self):
        prog_calls = []
        summary = library_service.scan_and_index(
            db=self.db,
            roots=[self.lib],
            ignore_rules=[],
            concurrency=2,
            do_fingerprint=True,
            progress=lambda done, total: prog_calls.append((done, total)),
        )
        self.assertEqual(summary.total_files, 3)
        # One duplicate detected by fingerprint (two duplicates total - one counted)
        self.assertGreaterEqual(summary.duplicates, 1)

        # Verify media files exist and duplicate files map to the same movie id
        mf1 = self.db.get_media_file_by_path(str(self.lib / "MovieA.2020.mkv"))
        mf2 = self.db.get_media_file_by_path(str(self.lib / "MovieA.2020.copy.mkv"))
        self.assertIsNotNone(mf1)
        self.assertIsNotNone(mf2)
        self.assertEqual(mf1.movie_id, mf2.movie_id)

        # Progress called 3 times
        self.assertEqual(len(prog_calls), 3)

    def test_scan_generates_poster_placeholder(self):
        video = self.lib / "Poster.Test.2022.mkv"
        video.write_bytes(b"fake video")
        library_service.scan_and_index(
            db=self.db,
            roots=[self.lib],
            ignore_rules=[],
            concurrency=1,
            do_fingerprint=True,
        )
        # Expect at least one poster image linked to the movie
        # Find movie by title
        m = self.db.get_movie_by_title_year("Poster Test", 2022)
        self.assertIsNotNone(m)
        imgs = self.db.get_images_for_movie(m.id, kind="poster")  # type: ignore[arg-type]
        self.assertTrue(len(imgs) >= 1)
        self.assertTrue(Path(imgs[0].path).exists())

    def test_scan_with_probe_and_rename_detection(self):
        # Initial scan with probe stub
        class StubInfo:
            def __init__(self):
                self.codec_name = "h264"
                self.width = 1920
                self.height = 1080
                self.channels = 2
                self.duration_sec = 321.0

        first = self.lib / "MovieC.2022.mkv"
        first.write_bytes(b"Z" * 4096)

        summary = library_service.scan_and_index(
            db=self.db,
            roots=[self.lib],
            ignore_rules=[],
            concurrency=1,
            do_fingerprint=True,
            progress=None,
            probe_func=lambda p: StubInfo(),
        )
        # Fetch the file from DB
        mf = self.db.get_media_file_by_path(str(first))
        self.assertIsNotNone(mf)
        self.assertEqual(mf.video_codec, "h264")
        self.assertEqual(mf.width, 1920)
        self.assertEqual(mf.height, 1080)
        self.assertEqual(mf.audio_channels, 2)

        # Movie runtime should be set
        mov = self.db.get_movie(mf.movie_id)
        self.assertIsNotNone(mov)
        self.assertEqual(mov.runtime_sec, 321)

        # Rename the file on disk; scan again and expect relink (no duplicate row)
        renamed = self.lib / "MovieC.2022.RENAMED.mkv"
        first.rename(renamed)
        summary2 = library_service.scan_and_index(
            db=self.db,
            roots=[self.lib],
            ignore_rules=[],
            concurrency=1,
            do_fingerprint=True,
            progress=None,
            probe_func=lambda p: StubInfo(),
        )
        mf2 = self.db.get_media_file_by_path(str(renamed))
        self.assertIsNotNone(mf2)
        self.assertEqual(mf2.movie_id, mf.movie_id)
        # Old path should not exist anymore in DB
        self.assertIsNone(self.db.get_media_file_by_path(str(first)))

    def test_relink_media_file_by_path(self):
        # Create file and scan
        p_old = self.lib / "Old.Title.2019.mkv"
        p_old.write_bytes(b"K" * 2048)
        library_service.scan_and_index(
            db=self.db,
            roots=[self.lib],
            ignore_rules=[],
            concurrency=1,
            do_fingerprint=False,
        )
        self.assertIsNotNone(self.db.get_media_file_by_path(str(p_old)))
        # Move file to new path and relink via DB helper
        p_new = self.lib / "Old.Title.2019.RELINKED.mkv"
        p_old.rename(p_new)
        ok = self.db.relink_media_file_by_path(str(p_old), str(p_new))
        self.assertTrue(ok)
        self.assertIsNone(self.db.get_media_file_by_path(str(p_old)))
        self.assertIsNotNone(self.db.get_media_file_by_path(str(p_new)))


if __name__ == "__main__":
    unittest.main()
