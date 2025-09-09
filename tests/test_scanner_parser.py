import os
import shutil
import tempfile
import unittest
from pathlib import Path

from infra import scanner, parser


class TestScannerParser(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="knotzflix_scan_"))
        # create structure
        (self.tmpdir / "Movies").mkdir()
        (self.tmpdir / "Movies" / "Extras").mkdir()
        (self.tmpdir / "Movies" / "Extras" / "clip.mkv").write_bytes(b"x")
        (self.tmpdir / "Movies" / "Blade.Runner.1982.1080p.mkv").write_bytes(b"x")
        (self.tmpdir / "Movies" / "sample.mkv").write_bytes(b"x")
        (self.tmpdir / ".hidden").mkdir()
        (self.tmpdir / ".hidden" / "Secret.mkv").write_bytes(b"x")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_scan_ignores_and_includes(self):
        items = scanner.scan([self.tmpdir], ignore_rules=["/Extras/"])
        paths = {i.path.name for i in items}
        self.assertIn("Blade.Runner.1982.1080p.mkv", paths)
        self.assertNotIn("clip.mkv", paths)  # Extras
        self.assertNotIn("sample.mkv", paths)  # sample.*
        self.assertNotIn("Secret.mkv", paths)  # hidden dir

    def test_parse_filename(self):
        title, year = parser.parse_filename("Blade.Runner.1982.1080p.mkv")
        self.assertEqual(title, "Blade Runner")
        self.assertEqual(year, 1982)
        sort = parser.make_sort_title("The Matrix")
        self.assertEqual(sort, "Matrix")


if __name__ == "__main__":
    unittest.main()

