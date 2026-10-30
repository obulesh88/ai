import json
import tempfile
import unittest
from pathlib import Path

from config import Config
from core.hema import Hema
from core.identity import Identity, IdentityError, clean_name
from tests.fake_ollama import start_server


def allow(action, detail):
    return True


class IdentityTests(unittest.TestCase):
    def test_defaults(self):
        identity = Identity()
        self.assertEqual(identity.assistant_name, "HEMA")
        self.assertEqual(identity.window_title(), "HEMA - Local AI Assistant")
        self.assertIn("You are HEMA", identity.system_prompt())
        self.assertIn("Obuleswar", identity.system_prompt())

    def test_greeting_by_hour(self):
        identity = Identity(user_name="Obuleswar")
        self.assertTrue(identity.greeting(hour=8).startswith("Good morning"))
        self.assertTrue(identity.greeting(hour=14).startswith("Good afternoon"))
        self.assertTrue(identity.greeting(hour=21).startswith("Good evening"))
        self.assertIn("I'm HEMA", identity.greeting(hour=21))

    def test_validation(self):
        with self.assertRaises(IdentityError):
            clean_name("   ", "name")
        with self.assertRaises(IdentityError):
            clean_name("x" * 40, "name")
        with self.assertRaises(IdentityError):
            clean_name("bad\x00name", "name")
        self.assertEqual(clean_name("  Jarvis   Prime ", "name"), "Jarvis Prime")
        with self.assertRaises(IdentityError):
            Identity(assistant_name="")

    def test_from_settings_falls_back_per_field(self):
        self.assertEqual(Identity.from_settings({}).assistant_name, "HEMA")
        partial = Identity.from_settings({"assistant_name": "", "user_name": "Sam"})
        # the invalid field falls back, the valid one is kept
        self.assertEqual((partial.assistant_name, partial.user_name), ("HEMA", "Sam"))
        broken = Identity.from_settings({"assistant_name": "x" * 40, "user_name": "Sam"})
        self.assertEqual((broken.assistant_name, broken.user_name), ("HEMA", "Sam"))
        self.assertEqual(Identity.from_settings("not a dict").assistant_name, "HEMA")
        good = Identity.from_settings({"assistant_name": "Jarvis", "user_name": "Sam"})
        self.assertEqual((good.assistant_name, good.user_name), ("Jarvis", "Sam"))

    def test_dict_roundtrip(self):
        identity = Identity("Jarvis", "Sam")
        self.assertEqual(Identity(**identity.to_dict()).to_dict(), identity.to_dict())


class IdentityIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.server, self.url, _ = start_server(("llama:latest",))
        self.addCleanup(self.server.shutdown)
        self.config = Config(self.url, "llama:latest", 5.0, 20, "sys",
                             workspace_dir=self.root / "ws", data_dir=self.root / "data",
                             logs_dir=self.root / "logs", backups_dir=self.root / "bk",
                             base_dir=self.root / "project")
        self.hema = Hema(self.config, allow)
        self.addCleanup(self.hema.close)

    def test_rename_applies_to_system_prompt_and_persists(self):
        data = self.hema.set_identity("Jarvis", "Sam")
        self.assertEqual(data, {"assistant_name": "Jarvis", "user_name": "Sam"})
        self.assertIn("You are Jarvis", self.hema.assistant.prompts.system_prompt)
        self.assertIn("Sam", self.hema.assistant.prompts.system_prompt)
        stored = json.loads((self.root / "data" / "settings.json").read_text())
        self.assertEqual(stored["assistant_name"], "Jarvis")

        hema2 = Hema(self.config, allow)
        self.addCleanup(hema2.close)
        self.assertEqual(hema2.identity.assistant_name, "Jarvis")
        self.assertIn("You are Jarvis", hema2.assistant.prompts.system_prompt)

    def test_partial_rename_keeps_the_other_name(self):
        self.hema.set_identity(assistant_name="Aria")
        self.assertEqual(self.hema.identity.user_name, "Obuleswar")
        self.hema.set_identity(user_name="Sam")
        self.assertEqual(self.hema.identity.assistant_name, "Aria")

    def test_invalid_rename_changes_nothing(self):
        before = self.hema.identity.to_dict()
        with self.assertRaises(IdentityError):
            self.hema.set_identity(assistant_name="   ")
        self.assertEqual(self.hema.identity.to_dict(), before)
        self.assertIn("You are HEMA", self.hema.assistant.prompts.system_prompt)

    def test_corrupt_settings_file_is_survivable(self):
        (self.root / "data").mkdir(parents=True, exist_ok=True)
        (self.root / "data" / "settings.json").write_text("{not json")
        hema = Hema(self.config, allow)
        self.addCleanup(hema.close)
        self.assertEqual(hema.identity.assistant_name, "HEMA")


if __name__ == "__main__":
    unittest.main()
