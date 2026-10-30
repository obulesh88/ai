import json
import tempfile
import unittest
from pathlib import Path

from interface.settings_store import DEFAULTS, load, save, settings_path


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name) / "data"

    def test_defaults_when_missing(self):
        self.assertEqual(load(self.data), DEFAULTS)

    def test_save_then_load_roundtrip(self):
        save(self.data, {"model": "qwen3.5:2b"})
        self.assertEqual(load(self.data)["model"], "qwen3.5:2b")
        self.assertTrue(settings_path(self.data).is_file())

    def test_unknown_keys_ignored(self):
        save(self.data, {"model": "a", "ollama_host": "http://evil", "nope": 1})
        saved = json.loads(settings_path(self.data).read_text())
        self.assertNotIn("ollama_host", saved)
        self.assertNotIn("nope", saved)
        self.assertEqual(saved["model"], "a")

    def test_partial_save_keeps_other_values(self):
        save(self.data, {"model": "m1", "ui_model": "u1"})
        save(self.data, {"model": "m2"})
        data = load(self.data)
        self.assertEqual((data["model"], data["ui_model"]), ("m2", "u1"))

    def test_timeout_persists(self):
        save(self.data, {"timeout": 45})
        self.assertEqual(load(self.data)["timeout"], 45)

    def test_corrupt_file_falls_back(self):
        settings_path(self.data).parent.mkdir(parents=True, exist_ok=True)
        settings_path(self.data).write_text("{not json")
        self.assertEqual(load(self.data), DEFAULTS)

    def test_wrong_types_ignored(self):
        settings_path(self.data).parent.mkdir(parents=True, exist_ok=True)
        settings_path(self.data).write_text(json.dumps({"model": [1, 2], "ui_model": "ok"}))
        data = load(self.data)
        self.assertEqual(data["model"], DEFAULTS["model"])
        self.assertEqual(data["ui_model"], "ok")


if __name__ == "__main__":
    unittest.main()
