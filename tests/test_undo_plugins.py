import json
import tempfile
import unittest
from pathlib import Path

from automation.file_manager import BackupManager, FileManager
from config import Config
from core.command_router import route
from core.hema import Hema
from core.outcome import Outcome, failed, ok, unverified
from core.plugin_loader import (PluginContext, PluginError, PluginRegistry, discover,
                                load_plugin_file)
from core.undo import UndoStack
from security.permissions import ApprovalManager, AuditLog, WorkspaceGuard
from tests.fake_ollama import start_server

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins"


def allow(action, detail):
    return True


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ws = self.root / "ws"
        self.audit = AuditLog(self.root / "audit.log")
        self.backups = BackupManager(self.root / "bk")
        self.undo = UndoStack()
        self.files = FileManager(WorkspaceGuard(self.ws),
                                 ApprovalManager(self.audit, allow),
                                 self.backups, undo=self.undo)


class OutcomeTests(unittest.TestCase):
    def test_helpers_and_speak(self):
        self.assertTrue(ok("done").ok)
        self.assertFalse(unverified("hmm").ok)
        self.assertEqual(failed("no").outcome, Outcome.FAILED)
        self.assertEqual(unverified("x").speak(), "[unverified] x")
        self.assertFalse(failed("x").ok)


class UndoStackTests(unittest.TestCase):
    def test_push_peek_history_clear(self):
        stack = UndoStack()
        self.assertFalse(stack.can_undo())
        stack.push("first", lambda: "did first")
        stack.push("second", lambda: "did second")
        self.assertEqual(stack.peek(), "second")
        self.assertEqual(stack.history(), ["second", "first"])
        self.assertEqual(len(stack), 2)
        stack.clear()
        self.assertFalse(stack.can_undo())

    def test_undo_last_reports_done(self):
        stack = UndoStack()
        stack.push("x", lambda: "reverted x")
        result = stack.undo_last()
        self.assertTrue(result.ok)
        self.assertIn("reverted x", result.detail)
        self.assertFalse(stack.can_undo())

    def test_empty_and_failures(self):
        stack = UndoStack()
        self.assertEqual(stack.undo_last().outcome, Outcome.FAILED)

        def boom():
            raise OSError("disk gone")

        stack.push("bad", boom)
        self.assertEqual(stack.undo_last().outcome, Outcome.FAILED)

        stack.push("unverifiable", lambda: "did it", verify=lambda: False)
        self.assertEqual(stack.undo_last().outcome, Outcome.UNVERIFIED)

    def test_max_items_keeps_newest(self):
        stack = UndoStack(max_items=3)
        for index in range(5):
            stack.push(f"a{index}", lambda: "x")
        self.assertEqual(stack.history(), ["a4", "a3", "a2"])


class UndoFileTests(Base):
    def test_undo_create_removes_file(self):
        self.files.write("notes.txt", "hello")
        self.assertTrue((self.ws / "notes.txt").is_file())
        result = self.undo.undo_last()
        self.assertTrue(result.ok, result)
        self.assertFalse((self.ws / "notes.txt").exists())

    def test_undo_overwrite_restores_content(self):
        self.files.write("a.txt", "v1")
        self.undo.clear()
        self.files.write("a.txt", "v2")
        self.assertEqual(self.files.read("a.txt"), "v2")
        self.assertTrue(self.undo.undo_last().ok)
        self.assertEqual(self.files.read("a.txt"), "v1")

    def test_undo_delete_restores_file(self):
        self.files.write("gone.txt", "important")
        self.undo.clear()
        self.files.delete("gone.txt")
        self.assertFalse((self.ws / "gone.txt").exists())
        self.assertTrue(self.undo.undo_last().ok)
        self.assertEqual(self.files.read("gone.txt"), "important")

    def test_without_stack_nothing_breaks(self):
        plain = FileManager(WorkspaceGuard(self.ws), ApprovalManager(self.audit, allow),
                            self.backups)
        plain.write("b.txt", "1")
        plain.write("b.txt", "2")
        self.assertEqual(plain.read("b.txt"), "2")


class PluginTests(Base):
    def make_plugin(self, name="good", body=None):
        directory = self.root / "plugins"
        directory.mkdir(exist_ok=True)
        body = body if body is not None else (
            "from core.outcome import ok\n"
            "TOOL = {'name': 'good', 'description': 'Does a useful thing on request', "
            "'parameters': {'type': 'OBJECT', 'properties': {}}}\n"
            "def run(args, ctx):\n"
            "    return ok('ran the good plugin')\n")
        path = directory / f"{name}.py"
        path.write_text(body)
        return path

    def test_loads_the_shipped_note_plugin(self):
        plugin = load_plugin_file(PLUGIN_DIR / "note_taker.py")
        self.assertEqual(plugin.name, "note")
        self.assertIn("note", plugin.description.lower())
        self.assertIn("text", plugin.parameters["properties"])

    def test_rejects_bad_plugins(self):
        cases = {
            "no_tool": "def run(args, ctx):\n    return None\n",
            "no_run": "TOOL = {'name': 'x', 'description': 'A plugin without a run callable'}\n",
            "bad_name": "TOOL = {'name': 'Bad Name', 'description': 'Names must be snake case'}\n"
                        "def run(args, ctx):\n    return None\n",
            "short_desc": "TOOL = {'name': 'x', 'description': 'short'}\n"
                          "def run(args, ctx):\n    return None\n",
            "broken": "TOOL = {'name': 'x',\n",
        }
        for name, body in cases.items():
            with self.subTest(name=name):
                path = self.make_plugin(name, body)
                with self.assertRaises(PluginError):
                    load_plugin_file(path)

    def test_discover_reports_problems_without_raising(self):
        self.make_plugin("good")
        self.make_plugin("bad", "raise RuntimeError('boom')\n")
        (self.root / "plugins" / "_template.py").write_text("raise SystemExit\n")
        plugins, problems = discover(self.root / "plugins")
        self.assertEqual([p.name for p in plugins], ["good"])
        self.assertTrue(any("bad.py" in problem for problem in problems))
        self.assertFalse(any("_template" in problem for problem in problems))

    def test_registry_refuses_reserved_duplicate_and_unknown(self):
        registry = PluginRegistry()
        self.make_plugin("good")
        registry.load_directory(self.root / "plugins")
        duplicate = self.make_plugin("dup", (
            "from core.outcome import ok\n"
            "TOOL = {'name': 'good', 'description': 'Duplicate name should be refused'}\n"
            "def run(args, ctx):\n    return ok('x')\n"))
        with self.assertRaises(PluginError):
            registry.register(load_plugin_file(duplicate))
        reserved = self.make_plugin("reserved", (
            "from core.outcome import ok\n"
            "TOOL = {'name': 'run', 'description': 'Reserved names must be refused'}\n"
            "def run(args, ctx):\n    return ok('x')\n"))
        with self.assertRaises(PluginError):
            registry.register(load_plugin_file(reserved))
        result = registry.run("missing", {}, PluginContext(root=self.ws))
        self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertIn("Unknown plugin", result.detail)

    def test_run_normalises_returns(self):
        ctx = PluginContext(root=self.ws, files=self.files)
        expectations = (
            (Outcome.DONE, "def run(a, c):\n    return 'plain string'\n"),
            (Outcome.UNVERIFIED, "def run(a, c):\n    return None\n"),
            (Outcome.FAILED, "def run(a, c):\n    raise ValueError('nope')\n"),
        )
        for expected, body in expectations:
            path = self.make_plugin("variant", (
                "TOOL = {'name': 'variant', 'description': 'Variant plugin for the test'}\n"
                + body))
            single = PluginRegistry()
            single.register(load_plugin_file(path))
            with self.subTest(expected=expected):
                self.assertEqual(single.run("variant", {}, ctx).outcome, expected)

    def test_note_plugin_writes_appends_and_undoes(self):
        registry = PluginRegistry()
        registry.register(load_plugin_file(PLUGIN_DIR / "note_taker.py"))
        ctx = PluginContext(root=self.ws, files=self.files)
        self.assertTrue(registry.run("note", {"text": "buy milk"}, ctx).ok)
        self.assertTrue(registry.run("note", {"text": "call mum"}, ctx).ok)
        content = self.files.read("notes.md")
        self.assertIn("buy milk", content)
        self.assertIn("call mum", content)
        self.assertEqual(content.count("- "), 2)
        self.assertTrue(self.undo.undo_last().ok)
        self.assertEqual(self.files.read("notes.md").count("- "), 1)

    def test_note_plugin_rejects_empty_text(self):
        registry = PluginRegistry()
        registry.register(load_plugin_file(PLUGIN_DIR / "note_taker.py"))
        result = registry.run("note", {}, PluginContext(root=self.ws, files=self.files))
        self.assertEqual(result.outcome, Outcome.FAILED)


class RouterTests(unittest.TestCase):
    def test_new_intents(self):
        self.assertEqual(route("undo").kind, "undo")
        self.assertEqual(route("Hey Hema, undo last").kind, "undo")
        self.assertEqual(route("what can you undo").kind, "undo_history")
        self.assertEqual(route("list plugins").kind, "plugin_list")
        intent = route("run plugin note buy milk")
        self.assertEqual(intent.kind, "plugin_run")
        self.assertEqual(intent.args["name"], "note")
        self.assertEqual(intent.args["args"], "buy milk")
        # the generic command intent must not swallow plugin requests
        self.assertEqual(route("run: echo hi").kind, "run_command")


class HemaIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        base = self.root / "project"
        (base / "plugins").mkdir(parents=True)
        (base / "plugins" / "echoer.py").write_text(
            "from core.outcome import ok\n"
            "TOOL = {'name': 'echoer', 'description': 'Echoes the text it is given'}\n"
            "def run(args, ctx):\n    return ok('echo: ' + str(args.get('text', '')))\n")
        self.base = base
        self.server, self.url, _ = start_server(("llama:latest",))
        self.addCleanup(self.server.shutdown)
        self.config = Config(self.url, "llama:latest", 5.0, 20, "sys",
                             workspace_dir=self.root / "ws", data_dir=self.root / "data",
                             logs_dir=self.root / "logs", backups_dir=self.root / "bk",
                             base_dir=base)
        self.hema = Hema(self.config, allow)
        self.addCleanup(self.hema.close)

    def test_plugin_runs_through_the_facade(self):
        self.assertEqual(self.hema.plugins.names(), ["echoer"])
        out = "".join(self.hema.handle("run plugin echoer hello there"))
        self.assertIn("[done]", out)
        self.assertIn("echo: hello there", out)

    def test_plugin_json_args(self):
        payload = json.dumps({"text": "json path"})
        out = "".join(self.hema.handle(f"run plugin echoer {payload}"))
        self.assertIn("echo: json path", out)

    def test_unknown_plugin_is_reported(self):
        out = "".join(self.hema.handle("run plugin nope"))
        self.assertIn("[failed]", out)
        self.assertIn("Unknown plugin", out)

    def test_undo_through_the_facade(self):
        self.hema.files.write("draft.txt", "first version")
        self.assertIn("create draft.txt", "".join(self.hema.handle("undo history")))
        out = "".join(self.hema.handle("undo"))
        self.assertIn("[done]", out)
        self.assertFalse((self.root / "ws" / "draft.txt").exists())
        self.assertIn("Nothing to undo", "".join(self.hema.handle("undo")))

    def test_list_plugins_through_the_facade(self):
        out = "".join(self.hema.handle("list plugins"))
        self.assertIn("echoer", out)
        self.assertIn("plugin(s) loaded", out)

    def test_broken_plugin_is_skipped_at_startup(self):
        (self.base / "plugins" / "broken.py").write_text("this is not python(\n")
        hema = Hema(self.config, allow)
        self.addCleanup(hema.close)
        self.assertIn("echoer", hema.plugins.names())
        self.assertTrue(any("broken.py" in problem for problem in hema.plugin_problems))
        self.assertIn("Skipped", "".join(hema.handle("list plugins")))


if __name__ == "__main__":
    unittest.main()
