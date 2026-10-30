"""Segment 12: end-to-end tests of the HEMA facade with a fake Ollama server."""
import tempfile
import unittest
from pathlib import Path

from config import Config
from core.command_router import route
from core.hema import Hema
from tests.fake_ollama import start_server


def allow(action, detail):
    return True


def deny(action, detail):
    return False


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.server, self.url, self.state = start_server(("qwen3-coder-local:latest",))
        self.addCleanup(self.server.shutdown)

    def config(self, host=None):
        return Config(host or self.url, "qwen3-coder-local:latest", 5.0, 20, "sys",
                      workspace_dir=self.root / "ws", data_dir=self.root / "data",
                      logs_dir=self.root / "logs", backups_dir=self.root / "bk")

    def hema(self, approver=allow, host=None):
        h = Hema(self.config(host), approver)
        self.addCleanup(h.close)
        return h


class RouterTests(unittest.TestCase):
    def test_intents(self):
        self.assertEqual(route("Hey Hema, update yourself").kind, "self_update")
        self.assertEqual(route("plan: build a snake game").args["request"], "build a snake game")
        self.assertEqual(route("show tasks").kind, "tasks")
        self.assertEqual(route("remember: I use Unity 2022").args["content"], "I use Unity 2022")
        self.assertEqual(route("recall Unity").args["text"], "Unity")
        self.assertEqual(route("forget 3").args["id"], "3")
        self.assertEqual(route("inspect: ./ws").args["text"], "./ws")
        self.assertEqual(route("open notepad").args["app"], "notepad")
        self.assertEqual(route("run: echo hi").args["text"], "echo hi")
        self.assertEqual(route("dragon result").args["outcome"], "dragon")
        self.assertEqual(route("dragon tiger stats").kind, "dt_stats")
        self.assertEqual(route("hello there").kind, "chat")
        self.assertEqual(route("   ").kind, "empty")


class FacadeTests(Base):
    def test_status_and_chat_memory(self):
        h = self.hema()
        h.assistant.models.select("qwen3-coder-local:latest")
        self.assertIn("workspace", h.status())
        reply = "".join(h.handle("hello"))
        self.assertEqual(reply, "reply1")
        msgs = h.memory.recent_messages()
        self.assertEqual([m["role"] for m in msgs], ["user", "assistant"])

    def test_remember_recall_forget(self):
        h = self.hema()
        out = "".join(h.handle("remember: I build games in Unity"))
        self.assertIn("Saved", out)
        self.assertIn("Unity", "".join(h.handle("recall Unity")))
        self.assertIn("Deleted", "".join(h.handle("forget 1")))
        self.assertIn("Nothing found", "".join(h.handle("recall Unity")))
        # remembering a note is not destructive, so it needs no approval
        self.assertIn("Saved", "".join(self.hema(deny).handle("remember: I like tea")))

    def test_forget_requires_approval(self):
        h = self.hema(deny)
        h.memory.add("note", "keep me")
        self.assertIn("Not approved", "".join(h.handle("forget 1")))
        self.assertEqual(len(h.memory.list()), 1)

    def test_plan_creates_tasks_and_lists(self):
        h = self.hema()
        out = "".join(h.handle("plan: make a pong game"))
        self.assertIn("created", out)
        self.assertTrue(h.tasks.list())
        self.assertIn("pending", "".join(h.handle("show tasks")))

    def test_dragon_tiger(self):
        h = self.hema()
        "".join(h.handle("dragon result"))
        out = "".join(h.handle("dragon tiger stats"))
        self.assertIn("1 rounds", out)
        self.assertIn("do not predict", out)

    def test_run_command_and_inspect(self):
        h = self.hema()
        out = "".join(h.handle("run: echo hello"))
        self.assertIn("exit=0", out)
        self.assertIn("hello", out)
        h.files.write("proj/main.py", "x = 1\n")
        self.assertIn('"type": "python"', "".join(h.handle("inspect: proj")))

    def test_blocked_command_is_rejected(self):
        h = self.hema()
        out = "".join(h.handle("run: format c:"))
        self.assertIn("PermissionDenied", out)

    def test_unapproved_app(self):
        h = self.hema()
        out = "".join(h.handle("open not-a-real-app"))
        self.assertIn("not in the approved app list", out)

    def test_ollama_down_is_reported_not_crashed(self):
        h = self.hema(host="http://127.0.0.1:1")
        out = "".join(h.handle("hello"))
        self.assertIn("Ollama error", out)

    def test_self_update_inspect(self):
        h = self.hema()
        proj = self.root / "proj"
        proj.mkdir()
        (proj / "a.py").write_text("x = 1\n")
        h.self_updater = h.self_updater.__class__(proj, h.approvals, h.backups,
                                                  python=__import__("sys").executable,
                                                  tests_dir=".")
        out = "".join(h.handle("update yourself"))
        self.assertIn("syntax_errors", out)
        self.assertIn("tests_ok", out)

    def test_close_twice_is_safe(self):
        h = Hema(self.config(), allow)
        h.close()


if __name__ == "__main__":
    unittest.main()
