import tempfile
import unittest
from pathlib import Path

from automation.app_manager import AppManager
from automation.command_runner import CommandRunner
from automation.file_manager import BackupManager, FileManager
from automation.startup import install_startup, remove_startup, startup_script
from core.executor import TaskExecutor
from core.planner import Planner, parse_plan
from core.task_manager import TaskManager
from security.permissions import ApprovalManager, AuditLog, PermissionDenied, WorkspaceGuard


def allow(action, detail):
    return True


def deny(action, detail):
    return False


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)


class TaskTests(Base):
    def setUp(self):
        super().setUp()
        self.tasks = TaskManager(self.root / "t.db")
        self.addCleanup(self.tasks.close)

    def test_create_progress_errors(self):
        tid = self.tasks.create("do it", ["a", "b"], ["fs"])
        self.tasks.set_progress(tid, 150)
        self.assertEqual(self.tasks.get(tid).progress, 100)
        self.tasks.add_error(tid, "boom")
        self.assertIn("boom", self.tasks.get(tid).errors)
        with self.assertRaises(ValueError):
            self.tasks.set_status(tid, "nonsense")
        with self.assertRaises(ValueError):
            self.tasks.create("   ")

    def test_recovery_after_restart(self):
        tid = self.tasks.create("crashy")
        self.tasks.set_status(tid, "running")
        self.tasks.close()
        tasks2 = TaskManager(self.root / "t.db")
        self.addCleanup(tasks2.close)
        recovered = tasks2.recover()
        self.assertEqual([t.id for t in recovered], [tid])
        self.assertEqual(recovered[0].status, "pending")

    def test_executor_success_verify_and_retry(self):
        tid = self.tasks.create("x")
        ex = TaskExecutor(self.tasks, {}, verifier=lambda r: (r == 5, "checked"))
        out = ex.run(tid, lambda: 5)
        self.assertEqual(out["status"], "done")
        self.assertTrue(out["verified"])

        state = {"n": 0}
        def flaky():
            state["n"] += 1
            if state["n"] < 2:
                raise RuntimeError("first fails")
            return "ok"
        tid2 = self.tasks.create("y")
        out2 = TaskExecutor(self.tasks, {}, max_retries=1).run(tid2, flaky)
        self.assertEqual(out2["status"], "done")
        self.assertEqual(self.tasks.get(tid2).attempts, 1)

    def test_executor_unverified_and_failure_and_cancel(self):
        tid = self.tasks.create("x")
        out = TaskExecutor(self.tasks, {}, verifier=lambda r: (False, "failed check")).run(tid, lambda: 1)
        self.assertEqual(out["status"], "done")
        self.assertFalse(out["verified"])
        tid2 = self.tasks.create("y")
        out2 = TaskExecutor(self.tasks, {}, max_retries=0).run(tid2, lambda: 1 / 0)
        self.assertEqual(out2["status"], "failed")
        tid3 = self.tasks.create("z")
        self.tasks.cancel(tid3)
        self.assertEqual(TaskExecutor(self.tasks, {}).run(tid3, lambda: 1)["status"], "cancelled")

    def test_executor_refuses_denied_tool(self):
        tid = self.tasks.create("x")
        def boom():
            raise PermissionDenied("no")
        out = TaskExecutor(self.tasks, {"t": boom}).run(tid, boom, "t")
        self.assertEqual(out["status"], "failed")
        with self.assertRaises(ValueError):
            TaskExecutor(self.tasks, {}).run(tid, lambda: 1, "missing")


class PlannerTests(unittest.TestCase):
    def test_parse_json_and_lines(self):
        self.assertEqual(parse_plan('["one","two"]'), ["one", "two"])
        self.assertEqual(parse_plan("1. a\n2) b"), ["a", "b"])
        self.assertEqual(parse_plan("no steps\nhere"), ["no steps", "here"])

    def test_fallback_when_model_fails(self):
        def bad(messages):
            raise RuntimeError("down")
        plan = Planner(bad).make_plan("build x")
        self.assertEqual(plan.source, "fallback")
        self.assertIn("build x", plan.steps[0])

    def test_model_plan(self):
        plan = Planner(lambda m: '["step1","step2"]').make_plan("x")
        self.assertEqual((plan.source, plan.steps), ("model", ["step1", "step2"]))


class AutomationTests(Base):
    def setUp(self):
        super().setUp()
        self.guard = WorkspaceGuard(self.root / "ws")
        self.audit = AuditLog(self.root / "audit.log")
        self.backups = BackupManager(self.root / "backups")
        self.files = FileManager(self.guard, ApprovalManager(self.audit, allow), self.backups)

    def test_write_read_backup_overwrite(self):
        self.files.write("a/b.txt", "v1")
        self.assertEqual(self.files.read("a/b.txt"), "v1")
        self.files.write("a/b.txt", "v2")
        self.assertEqual(self.files.read("a/b.txt"), "v2")
        self.assertEqual(len(list((self.root / "backups").iterdir())), 1)
        self.assertEqual(self.files.list(), ["a"])
        self.assertEqual(self.files.list("a"), ["a/b.txt"])

    def test_write_denied_and_secret_blocked(self):
        f = FileManager(self.guard, ApprovalManager(self.audit, deny), self.backups)
        f.write("x.txt", "1")
        with self.assertRaises(PermissionDenied):
            f.write("x.txt", "2")
        with self.assertRaises(ValueError):
            f.write("secret.txt", "api_key=abc")

    def test_delete_needs_approval_and_restores(self):
        self.files.write("d.txt", "data")
        backup = self.files.delete("d.txt")
        self.assertFalse((self.guard.root / "d.txt").exists())
        with self.assertRaises(FileNotFoundError):
            self.files.delete("d.txt")
        self.backups.restore(backup, self.guard.root / "d.txt")
        self.assertEqual(self.files.read("d.txt"), "data")
        with self.assertRaises(PermissionDenied):
            self.files.read("../../etc/passwd")

    def test_command_runner(self):
        runner = CommandRunner(ApprovalManager(self.audit, allow), self.guard)
        code, out = runner.run("echo hello")
        self.assertEqual(code, 0)
        self.assertIn("hello", out)
        for bad in ("format c:", "net user bob /add", "Set-MpPreference -DisableRealtimeMonitoring $true", "sudo ls"):
            with self.assertRaises(PermissionDenied):
                runner.check_allowed(bad)
        deny_runner = CommandRunner(ApprovalManager(self.audit, deny), self.guard)
        with self.assertRaises(PermissionDenied):
            deny_runner.run("echo hi")

    def test_command_runner_redacts(self):
        runner = CommandRunner(ApprovalManager(self.audit, allow), self.guard)
        _, out = runner.run('echo "token=abc123"')
        self.assertNotIn("abc123", out)

    def test_app_manager(self):
        apps = AppManager(ApprovalManager(self.audit, deny), {"echo": "echo"})
        with self.assertRaises(PermissionDenied):
            apps.launch("echo")
        with self.assertRaises(PermissionDenied):
            apps.launch("not-allowed")

    def test_startup(self):
        target = self.root / "startup"
        approvals = ApprovalManager(self.audit, allow)
        script = install_startup(self.root, approvals, target)
        text = script.read_text(encoding="utf-8")
        self.assertIn("main.py --gui", text)
        self.assertIn("cd /d", text)
        self.assertIn("main.py", startup_script(self.root))
        self.assertTrue(remove_startup(approvals, target))
        self.assertFalse(remove_startup(approvals, target))


if __name__ == "__main__":
    unittest.main()
