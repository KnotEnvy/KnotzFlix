import importlib
import unittest


class TestSanity(unittest.TestCase):
    def test_import_packages(self):
        importlib.import_module("ui")
        importlib.import_module("domain")
        importlib.import_module("infra")

    def test_truth(self):
        self.assertTrue(True)
