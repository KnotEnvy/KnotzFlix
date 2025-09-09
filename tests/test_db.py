import os
import shutil
import tempfile
import unittest
from pathlib import Path

from domain.models import Movie, MediaFile, Image, PlayState
from infra import db as dbmod
from infra import paths


class TestDB(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="knotzflix_db_"))
        os.environ[paths.ENV_DATA_DIR] = str(self.tmpdir)
        self.db = dbmod.Database()
        self.db.initialize()

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass
        os.environ.pop(paths.ENV_DATA_DIR, None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_schema_version_and_crud(self):
        # Schema version exists (version 1)
        cur = self.db.conn.execute("SELECT version FROM schema_version")
        ver = cur.fetchone()[0]
        self.assertGreaterEqual(ver, 1)

        # Add movie
        mid = self.db.add_movie(Movie(id=None, canonical_title="Inception", year=2010, sort_title="Inception"))
        got = self.db.get_movie(mid)
        self.assertIsNotNone(got)
        self.assertEqual(got.canonical_title, "Inception")

        # Update title
        self.db.update_movie_title(mid, "Inception (Remastered)")
        got2 = self.db.get_movie(mid)
        self.assertEqual(got2.canonical_title, "Inception (Remastered)")

        # Add media file
        f_id = self.db.add_media_file(
            MediaFile(id=None, movie_id=mid, path="C:/movies/Inception.mkv", size_bytes=123, mtime_ns=0)
        )
        self.assertTrue(f_id > 0)

        # Add image
        img_id = self.db.add_image(Image(id=None, movie_id=mid, kind="poster", path="/cache/posters/abc.jpg"))
        self.assertTrue(img_id > 0)

        # Play state upsert
        self.db.set_play_state(PlayState(movie_id=mid, position_sec=42, watched=False))
        self.db.set_play_state(PlayState(movie_id=mid, position_sec=84, watched=True))
        row = self.db.conn.execute("SELECT position_sec, watched FROM play_state WHERE movie_id=?", (mid,)).fetchone()
        self.assertEqual(row[0], 84)
        self.assertEqual(row[1], 1)

    def test_search(self):
        mid = self.db.add_movie(Movie(id=None, canonical_title="Blade Runner", year=1982, sort_title="Blade Runner"))
        ids = self.db.search_titles("Blade")
        self.assertIn(mid, ids)


if __name__ == "__main__":
    unittest.main()
