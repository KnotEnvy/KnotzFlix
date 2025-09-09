import json
import unittest
from pathlib import Path

from infra.ffprobe import parse_ffprobe_json, MediaInfo


class TestFFProbe(unittest.TestCase):
    def test_parse_ffprobe_json(self):
        p = Path("tests/fixtures/ffprobe_sample.json")
        data = json.loads(p.read_text(encoding="utf-8"))
        info = parse_ffprobe_json(data)
        self.assertIsInstance(info, MediaInfo)
        self.assertEqual(info.codec_name, "h264")
        self.assertEqual(info.width, 1920)
        self.assertEqual(info.height, 1080)
        self.assertEqual(info.channels, 6)
        self.assertAlmostEqual(info.duration_sec or 0.0, 123.456, places=3)


if __name__ == "__main__":
    unittest.main()

