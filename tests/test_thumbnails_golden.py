import unittest

from infra import thumbnails


class TestThumbnailsGolden(unittest.TestCase):
    def test_deterministic_timestamp_simple(self):
        # Same fingerprint + duration should yield same ts
        ts1 = thumbnails.choose_timestamp_deterministic("a" * 64, 120.0)
        ts2 = thumbnails.choose_timestamp_deterministic("a" * 64, 120.0)
        self.assertAlmostEqual(ts1, ts2, places=6)

    def test_different_fingerprints_offset_differs(self):
        ts_a = thumbnails.choose_timestamp_deterministic("a" * 64, 200.0)
        ts_b = thumbnails.choose_timestamp_deterministic("b" * 64, 200.0)
        self.assertNotEqual(ts_a, ts_b)
        # Both within clamped bounds [10, duration-5]
        self.assertGreaterEqual(ts_a, 10.0)
        self.assertLessEqual(ts_a, 195.0)
        self.assertGreaterEqual(ts_b, 10.0)
        self.assertLessEqual(ts_b, 195.0)

    def test_short_duration_clamping(self):
        # Very short duration should clamp near 10s to duration-5s bound
        ts = thumbnails.choose_timestamp_deterministic("f" * 64, 12.0)
        self.assertGreaterEqual(ts, 10.0)
        self.assertLessEqual(ts, 7.0 + 5.0)  # duration-5 = 7.0, max applied in chooser


if __name__ == "__main__":
    unittest.main()

