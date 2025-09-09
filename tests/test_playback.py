import unittest
from pathlib import Path

from infra.playback import build_launch_command, build_reveal_command


class TestPlaybackCommands(unittest.TestCase):
    def test_build_launch_command_windows(self):
        cmd = build_launch_command(Path("C:/Movies/Inception.mkv"), platform="win")
        self.assertEqual(cmd[:3], ["cmd", "/c", "start"])
        self.assertEqual(cmd[3], "")
        self.assertIn("Inception.mkv", cmd[4])

    def test_build_launch_command_macos(self):
        cmd = build_launch_command(Path("/Movies/Inception.mkv"), platform="darwin")
        self.assertEqual(cmd[0], "open")

    def test_build_launch_command_linux(self):
        cmd = build_launch_command(Path("/home/user/Inception.mkv"), platform="linux")
        self.assertEqual(cmd[0], "xdg-open")

    def test_build_reveal_command_windows(self):
        cmd = build_reveal_command(Path("C:/Movies/Inception.mkv"), platform="win")
        self.assertEqual(cmd[0], "explorer")
        self.assertEqual(cmd[1], "/select,")

    def test_build_reveal_command_macos(self):
        cmd = build_reveal_command(Path("/Movies/Inception.mkv"), platform="darwin")
        self.assertEqual(cmd[:2], ["open", "-R"])

    def test_build_reveal_command_linux(self):
        cmd = build_reveal_command(Path("/home/user/Inception.mkv"), platform="linux")
        self.assertEqual(cmd[0], "xdg-open")
        self.assertTrue(cmd[1].endswith("/home/user"))


if __name__ == "__main__":
    unittest.main()

