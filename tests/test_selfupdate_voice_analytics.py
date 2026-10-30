import tempfile
import unittest
from pathlib import Path

from analytics.dragon_tiger import DragonTigerStore, wilson_interval
from automation.file_manager import BackupManager
from core.self_update import SelfUpdater
from security.permissions import ApprovalManager, AuditLog, PermissionDenied
from voice.speech import PrintSpeaker
from voice.voice_controller import VoiceController
from voice.wake_word import extract_command, has_wake_word


def allow(a, d):
    return True


def deny(a, d):
    return False


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)


class SelfUpdateTests(Base):
    def make_project(self, body="VALUE = 1\n"):
        (self.root / "mod.py").write_text(body)
        (self.root / "tests").mkdir(exist_ok=True)
        (self.root / "tests" / "test_mod.py").write_text(
            "import unittest, mod\n"
            "class T(unittest.TestCase):\n"
            "    def test_v(self):\n"
            "        self.assertEqual(mod.VALUE, 1)\n")
        (self.root / "tests" / "__init__.py").write_text("")
        self.approvals = ApprovalManager(AuditLog(self.root / "audit.log"), allow)
        self.backups = BackupManager(self.root / "bk")
        self.updater = SelfUpdater(self.root, self.approvals, self.backups, tests_dir="tests")

    def test_inspect_clean(self):
        self.make_project()
        info = self.updater.inspect()
        self.assertEqual(info["syntax_errors"], {})
        self.assertTrue(info["tests_ok"], info["test_output"])

    def test_apply_good_change(self):
        self.make_project()
        out = self.updater.apply({"mod.py": "VALUE = 1\nEXTRA = 2\n"})
        self.assertTrue(out["ok"], out)
        self.assertIn("EXTRA", (self.root / "mod.py").read_text())

    def test_syntax_error_rolls_back(self):
        self.make_project()
        out = self.updater.apply({"mod.py": "def broken(:\n"})
        self.assertFalse(out["ok"])
        self.assertTrue(out["rolled_back"])
        self.assertIn("VALUE = 1", (self.root / "mod.py").read_text())

    def test_failing_test_rolls_back_and_removes_new_file(self):
        self.make_project()
        out = self.updater.apply({"mod.py": "VALUE = 2\n", "newfile.py": "x = 1\n"})
        self.assertFalse(out["ok"])
        self.assertTrue(out["rolled_back"])
        self.assertIn("VALUE = 1", (self.root / "mod.py").read_text())
        self.assertFalse((self.root / "newfile.py").exists())

    def test_denied_update_changes_nothing(self):
        self.make_project()
        denied = SelfUpdater(self.root, ApprovalManager(AuditLog(self.root / "a2.log"), deny),
                             self.backups, tests_dir="tests")
        with self.assertRaises(PermissionDenied):
            denied.apply({"mod.py": "VALUE = 9\n"})
        self.assertIn("VALUE = 1", (self.root / "mod.py").read_text())

    def test_security_change_requires_extra_approval(self):
        self.make_project()
        (self.root / "security").mkdir()
        (self.root / "security" / "p.py").write_text("X = 1\n")
        calls = []
        def approver(action, detail):
            calls.append(action)
            return action != "security-change"
        up = SelfUpdater(self.root, ApprovalManager(AuditLog(self.root / "a3.log"), approver),
                         self.backups, tests_dir="tests")
        with self.assertRaises(PermissionDenied):
            up.apply({"security/p.py": "X = 2\n"})
        self.assertIn("security-change", calls)

    def test_path_escape_blocked(self):
        self.make_project()
        with self.assertRaises(PermissionDenied):
            self.updater.apply({"../evil.py": "x=1\n"})


class AnalyticsTests(Base):
    def setUp(self):
        super().setUp()
        self.s = DragonTigerStore(self.root / "dt.db")
        self.addCleanup(self.s.close)

    def test_add_validate_and_counts(self):
        for o in ["dragon", "dragon", "tiger", "tie", "dragon"]:
            self.s.add(o)
        with self.assertRaises(ValueError):
            self.s.add("monkey")
        s = self.s.summary()
        self.assertEqual(s["total"], 5)
        self.assertEqual(s["counts"], {"dragon": 3, "tiger": 1, "tie": 1})
        self.assertAlmostEqual(s["stats"]["dragon"]["percent"], 60.0)
        lo, hi = s["stats"]["dragon"]["ci95"]
        self.assertTrue(lo < 60 < hi)
        self.assertIn("do not predict", s["disclaimer"])

    def test_streaks_and_delete(self):
        for o in ["tiger", "tiger", "tiger", "dragon"]:
            self.s.add(o)
        self.assertEqual(self.s.summary()["streaks"]["longest"]["tiger"], 3)
        rid = self.s.all()[0]["id"]
        self.assertTrue(self.s.delete(rid))
        self.assertFalse(self.s.delete(rid))
        self.assertEqual(self.s.summary()["total"], 3)

    def test_empty_and_text_and_bulk(self):
        s = self.s.summary()
        self.assertEqual(s["total"], 0)
        self.assertEqual(s["stats"]["dragon"]["percent"], 0.0)
        self.assertIn("0 rounds", self.s.report_text())
        self.assertEqual(self.s.add_many(["dragon", "tiger"]), 2)
        self.assertIn("Dragon", self.s.report_text())

    def test_wilson_interval(self):
        lo, hi = wilson_interval(0, 0)
        self.assertEqual((lo, hi), (0.0, 1.0))
        lo, hi = wilson_interval(50, 100)
        self.assertTrue(0.40 < lo < 0.50 and 0.50 < hi < 0.60)


class VoiceTests(unittest.TestCase):
    def test_wake_word(self):
        self.assertTrue(has_wake_word("Hey Hema, open notepad"))
        self.assertTrue(has_wake_word("hey, hema"))
        self.assertFalse(has_wake_word("hello there"))
        self.assertEqual(extract_command("Hey Hema, open notepad"), "open notepad")
        self.assertEqual(extract_command("open notepad"), "")

    def test_controller_permission_and_commands(self):
        got = []
        vc = VoiceController(lambda: None, PrintSpeaker(),
                             ApprovalManager(AuditLog(Path(tempfile.mkdtemp()) / "a.log"), deny))
        with self.assertRaises(PermissionDenied):
            vc.start()
        self.assertFalse(vc.listening)

        vc2 = VoiceController(lambda: None, PrintSpeaker(),
                              ApprovalManager(AuditLog(Path(tempfile.mkdtemp()) / "a.log"), allow))
        vc2.on_command = got.append
        self.assertEqual(vc2.handle_transcript("Hey Hema tell me a joke"), "tell me a joke")
        self.assertIsNone(vc2.handle_transcript("unrelated speech"))
        vc3 = VoiceController(lambda: None, PrintSpeaker(), vc2.approvals, require_wake_word=False)
        self.assertEqual(vc3.handle_transcript("do it"), "do it")
        self.assertIsNone(vc3.handle_transcript("  "))

    def test_print_speaker(self):
        PrintSpeaker().speak("hello")


if __name__ == "__main__":
    unittest.main()
