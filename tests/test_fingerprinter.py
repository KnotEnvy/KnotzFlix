import os
import shutil
import tempfile
import unittest
from pathlib import Path

from infra.fingerprinter import fingerprint_partial


class TestFingerprinter(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="knotzflix_fp_"))
        self.file1 = self.tmpdir / "a.bin"
        self.file2 = self.tmpdir / "b.bin"
        self.file1.write_bytes(b"A" * 1024 + b"B" * 1024 + b"C" * 1024)
        self.file2.write_bytes(b"A" * 1024 + b"B" * 1024 + b"D" * 1024)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_fingerprint_partial_differs(self):
        fp1 = fingerprint_partial(self.file1, bytes_per_chunk=256, chunks=3)
        fp2 = fingerprint_partial(self.file2, bytes_per_chunk=256, chunks=3)
        self.assertNotEqual(fp1, fp2)


if __name__ == "__main__":
    unittest.main()

