from __future__ import annotations

import unittest

from infra import thumbnails as th


class TestPosterScoringGolden(unittest.TestCase):
    def test_parse_signalstats_line(self):
        text = "... signalstats: YAVG:123.4 YMIN:5 YMAX:245 other"
        vals = th._parse_signalstats(text)
        self.assertAlmostEqual(vals.get("YAVG", 0.0), 123.4, places=1)
        self.assertEqual(vals.get("YMIN"), 5.0)
        self.assertEqual(vals.get("YMAX"), 245.0)

    def test_score_timestamp_deterministic_with_mocked_stats(self):
        # Monkeypatch the internal ffmpeg stats function

        def fake_stats(_media_path, ts_sec: float, *, filter_chain: str):
            # Base stats: mid brightness around 128, dynamic range varies with ts
            if "edgedetect" in filter_chain:
                # Simulate higher edge strength for larger timestamp
                yavg = min(255.0, 100.0 + ts_sec % 50)
                return {"YAVG": yavg, "YMIN": 0.0, "YMAX": 255.0}
            else:
                # Prefer mid brightness; dynamic range slightly higher for higher ts
                yavg = 128.0 + ((ts_sec % 7) - 3)  # stays near 128
                ymin = 10.0
                ymax = min(255.0, 200.0 + (ts_sec % 20))
                return {"YAVG": yavg, "YMIN": ymin, "YMAX": ymax}

        old = th._ffmpeg_signalstats
        try:
            th._ffmpeg_signalstats = fake_stats  # type: ignore[attr-defined]
            s1 = th._score_timestamp(th.Path("/dev/null"), 10.0)
            s2 = th._score_timestamp(th.Path("/dev/null"), 30.0)
            self.assertIsNotNone(s1)
            self.assertIsNotNone(s2)
            # Expect later timestamp to score >= due to higher edge/dyn range in our fake
            self.assertGreaterEqual(s2, s1)
        finally:
            th._ffmpeg_signalstats = old  # type: ignore[attr-defined]

