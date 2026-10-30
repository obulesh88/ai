import json
import sys
import tempfile
import unittest
from pathlib import Path

from automation.file_manager import BackupManager, FileManager
from coding.code_agent import CodeAgent, extract_code
from coding.code_editor import CodeEditor
from coding.project_inspector import detect_type, index_python_symbols, inspect_project, syntax_check_python
from coding.test_runner import summarize_test_output
from game_development import mcp_integration as mcp
from game_development.unity import UnityProject
from game_development.unreal import UnrealProject
from security.permissions import ApprovalManager, AuditLog, WorkspaceGuard


def allow(a, d):
    return True


def deny(a, d):
    return False


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ws = self.root / "ws"
        self.files = FileManager(WorkspaceGuard(self.ws),
                                 ApprovalManager(AuditLog(self.root / "a.log"), allow),
                                 BackupManager(self.root / "bk"))
        self.editor = CodeEditor(self.files)

    def unity_project(self):
        p = self.root / "Game"
        (p / "ProjectSettings").mkdir(parents=True)
        (p / "ProjectSettings" / "ProjectVersion.txt").write_text("m_EditorVersion: 2022.3.10f1\n")
        (p / "Assets" / "Scenes").mkdir(parents=True)
        (p / "Assets" / "Scenes" / "Main.unity").write_text(
            "GameObject:\n  m_Name: Player\n  m_Name: Enemy\n")
        return p

    def unreal_project(self):
        p = self.root / "UProject"
        (p / "Source" / "MyGame").mkdir(parents=True)
        (p / "Source" / "MyGame" / "MyGame.Build.cs").write_text("// build")
        (p / "MyGame.uproject").write_text("{" + '"FileVersion":3' + "}")
        return p


class InspectorTests(Base):
    def test_inspect_python_project(self):
        self.files.write("main.py", "def run():\n    return 1\n")
        self.files.write("bad.py" if False else "good.py", "x = 1\n")
        info = inspect_project(self.ws)
        self.assertEqual(info["type"], "python")
        self.assertEqual(info["file_count"], 2)
        self.assertEqual(syntax_check_python(self.ws), {})
        self.assertIn("Function run", index_python_symbols(self.ws / "main.py"))

    def test_syntax_error_detected(self):
        self.files.write("bad.py", "def broken(:\n")
        errors = syntax_check_python(self.ws)
        self.assertIn("bad.py", errors)

    def test_detect_unity_and_unreal(self):
        u = self.unity_project()
        self.assertEqual(detect_type(u), "unity")
        info = inspect_project(u)
        self.assertEqual(info["unity"]["version"], "2022.3.10f1")
        self.assertIn("Assets/Scenes/Main.unity", info["unity"]["scenes"])
        self.assertEqual(detect_type(self.unreal_project()), "unreal")
        with self.assertRaises(FileNotFoundError):
            inspect_project(self.root / "nope")


class EditorTests(Base):
    def test_replace_exactly_once(self):
        self.files.write("m.py", "a = 1\n")
        self.editor.replace("m.py", "a = 1", "a = 2")
        self.assertEqual(self.files.read("m.py"), "a = 2\n")
        self.files.write("m.py", "x\nx\n")
        with self.assertRaises(ValueError):
            self.editor.replace("m.py", "x", "y")
        with self.assertRaises(ValueError):
            self.editor.replace("m.py", "zzz", "y")
        self.assertEqual(self.editor.append("m.py", "end\n").read_text()[-4:], "end\n")

    def test_edit_of_existing_needs_approval(self):
        self.files.write("m.py", "a = 1\n")
        locked = CodeEditor(FileManager(WorkspaceGuard(self.ws),
                                        ApprovalManager(AuditLog(self.root / "b.log"), deny),
                                        BackupManager(self.root / "bk2")))
        with self.assertRaises(Exception):
            locked.replace("m.py", "a = 1", "a = 3")


class AgentTests(Base):
    def test_generate_valid_and_invalid(self):
        agent = CodeAgent(lambda m: "```python\ndef f():\n    return 1\n```", self.editor, self.ws)
        out = agent.generate_file("new.py", "make f")
        self.assertTrue(out["ok"])
        self.assertIsNone(out["syntax_error"])
        bad = CodeAgent(lambda m: "```python\ndef f(:\n```", self.editor, self.ws)
        out2 = bad.generate_file("bad.py", "make bad")
        self.assertFalse(out2["ok"])
        self.assertIsNotNone(out2["syntax_error"])
        self.assertFalse(CodeAgent(lambda m: "", self.editor, self.ws).generate_file("e.py", "x")["ok"])

    def test_fix_syntax_error(self):
        self.files.write("broken.py", "def f(:\n")
        agent = CodeAgent(lambda m: "```python\ndef f():\n    return 2\n```", self.editor, self.ws)
        out = agent.fix_syntax_error(self.ws / "broken.py")
        self.assertTrue(out["ok"], out)
        self.assertEqual(self.files.read("broken.py"), "def f():\n    return 2\n")

    def test_extract_code(self):
        self.assertEqual(extract_code("```python\nx=1\n```"), "x=1\n")
        self.assertEqual(extract_code("plain"), "plain")
        self.assertIsNone(extract_code("   "))

    def test_summarize(self):
        self.assertIn("Ran 3 tests; OK", summarize_test_output("Ran 3 tests in 0.1s\n\nOK"))
        self.assertIn("FAILED", summarize_test_output("Ran 1 test\nFAILED (failures=1)"))


class UnityTests(Base):
    def test_project(self):
        u = UnityProject(self.unity_project())
        self.assertEqual(u.editor_version(), "2022.3.10f1")
        self.assertEqual(u.scenes(), ["Assets/Scenes/Main.unity"])
        self.assertEqual(u.scene_objects("Assets/Scenes/Main.unity"), ["Player", "Enemy"])
        self.assertEqual(u.scripts(), [])

    def test_create_script(self):
        u = UnityProject(self.unity_project())
        path = u.create_script("PlayerController", "void Update() { }")
        text = path.read_text()
        self.assertIn("class PlayerController : MonoBehaviour", text)
        self.assertIn("void Update() { }", text)
        self.assertIn("Assets/Scripts/PlayerController.cs", u.scripts())
        with self.assertRaises(ValueError):
            u.create_script("bad name;")

    def test_errors_and_rejects_non_unity(self):
        self.assertEqual(UnityProject.parse_console_errors("ok\nerror CS1002: ; expected\n"),
                         ["error CS1002: ; expected"])
        with self.assertRaises(ValueError):
            UnityProject(self.root)


class UnrealTests(Base):
    def test_find_modules_and_create(self):
        root = self.unreal_project()
        up = UnrealProject(UnrealProject.find(root))
        self.assertEqual(up.modules(), ["MyGame"])
        out = up.create_cpp_class("HealthActor", "MyGame")
        self.assertTrue(out["header"].read_text().startswith("#pragma once"))
        self.assertIn("MYGAME_API AHealthActor", out["header"].read_text())
        self.assertIn("AHealthActor::AHealthActor()", out["source"].read_text())
        with self.assertRaises(FileExistsError):
            up.create_cpp_class("HealthActor", "MyGame")
        with self.assertRaises(FileNotFoundError):
            up.create_cpp_class("X", "NoModule")
        with self.assertRaises(ValueError):
            up.create_cpp_class("bad-name", "MyGame")

    def test_build_command_and_errors(self):
        up = UnrealProject(UnrealProject.find(self.unreal_project()))
        cmd = up.build_command("C:/UE")
        self.assertIn("RunUAT.bat", cmd)
        self.assertIn("MyGame.uproject", cmd)
        self.assertEqual(UnrealProject.parse_build_errors("error C2065: 'x': undeclared"),
                         ["error C2065: 'x': undeclared"])
        with self.assertRaises(ValueError):
            UnrealProject(self.root / "x.txt")


class McpTests(Base):
    def test_load_and_describe(self):
        cfg = self.root / "mcp.json"
        cfg.write_text(json.dumps({"mcpServers": {
            "unity": {"command": "nope-not-real", "args": ["--x"]},
            "py": {"command": sys.executable}}}))
        servers = mcp.load_servers([str(cfg), str(self.root / "missing.json")])
        info = {d["name"]: d for d in mcp.describe(servers)}
        self.assertFalse(info["unity"]["command_found"])
        self.assertTrue(info["py"]["command_found"])

    def test_probe_missing_command(self):
        out = mcp.probe({"command": "definitely-not-a-real-binary"})
        self.assertFalse(out["connected"])
        self.assertIn("not found", out["error"])

    def test_probe_real_fake_server(self):
        server = self.root / "srv.py"
        server.write_text(
            "import sys, json\n"
            "for line in sys.stdin:\n"
            "    req = json.loads(line)\n"
            "    if req['method'] == 'initialize':\n"
            "        print(json.dumps({'jsonrpc':'2.0','id':req['id'],'result':{'serverInfo':{'name':'fake'}}}), flush=True)\n"
            "    elif req['method'] == 'tools/list':\n"
            "        print(json.dumps({'jsonrpc':'2.0','id':req['id'],'result':{'tools':[{'name':'make_object'}]}}), flush=True)\n")
        out = mcp.probe({"command": sys.executable, "args": [str(server)]})
        self.assertTrue(out["connected"], out)
        self.assertEqual(out["tools"], ["make_object"])


if __name__ == "__main__":
    unittest.main()
