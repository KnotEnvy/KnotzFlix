from __future__ import annotations

import unittest

from infra.thumbnails import (
    choose_candidate_timestamps,
    choose_timestamp_deterministic,
)


class TestPosterHeuristicsGolden(unittest.TestCase):
    def test_candidates_deterministic_and_bounded(self):
        dur = 7200.0  # 2 hours
        fp = "abc123"
        c1 = choose_candidate_timestamps(fp, dur, count=5)
        c2 = choose_candidate_timestamps(fp, dur, count=5)
        self.assertEqual(c1, c2)
        self.assertTrue(1 <= len(c1) <= 5)
        # All within [10, dur-5]
        for t in c1:
            self.assertGreaterEqual(t, 10.0)
            self.assertLessEqual(t, dur - 5.0)
        # Sorted increasing
        self.assertEqual(c1, sorted(c1))

    def test_candidates_change_with_fingerprint(self):
        dur = 3600.0
        c1 = choose_candidate_timestamps("alpha", dur, count=5)
        c2 = choose_candidate_timestamps("beta", dur, count=5)
        self.assertNotEqual(c1, c2)

    def test_base_included(self):
        dur = 3000.0
        fp = "seed-xyz"
        base = round(choose_timestamp_deterministic(fp, dur), 2)
        cand = choose_candidate_timestamps(fp, dur, count=5)
        self.assertIn(base, cand)

