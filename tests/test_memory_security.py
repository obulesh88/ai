import tempfile
import threading
import time
import unittest
from pathlib import Path

from memory.memory_manager import MemoryManager
from security.permissions import (ApprovalManager, AuditLog, PermissionDenied, QueueApprover,
                                  WorkspaceGuard, redact)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "m.db"
        self.m = MemoryManager(self.path)
        self.addCleanup(self.m.close)

    def test_crud_and_search(self):
        i = self.m.add("preference", "I like dark mode")
        self.assertEqual(len(self.m.search("dark")), 1)
        self.assertTrue(self.m.update(i, "I like light mode"))
        self.assertEqual(self.m.search("light")[0]["content"], "I like light mode")
        self.assertTrue(self.m.delete(i))
        self.assertEqual(self.m.list(), [])
        self.assertFalse(self.m.delete(i))

    def test_rejects_secrets_and_bad_kind(self):
        with self.assertRaises(ValueError):
            self.m.add("note", "my password: hunter2")
        with self.assertRaises(ValueError):
            self.m.add("bogus", "x")
        self.m.add_message("user", "api_key=abc123")
        self.assertNotIn("abc123", self.m.recent_messages()[0]["content"])

    def test_persists_across_restart(self):
        self.m.add("project", "HEMA")
        self.m.add_message("user", "hi")
        self.m.close()
        m2 = MemoryManager(self.path)
        self.addCleanup(m2.close)
        self.assertEqual(m2.list()[0]["content"], "HEMA")
        self.assertEqual(m2.recent_messages()[0]["content"], "hi")
        self.m = m2

    def test_search_is_literal(self):
        self.m.add("note", "100% done")
        self.m.add("note", "other")
        self.assertEqual(len(self.m.search("%")), 1)


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_guard(self):
        g = WorkspaceGuard(self.root / "ws")
        self.assertTrue(str(g.resolve("a/b.txt")).startswith(str(g.root)))
        for bad in ("../x", "/etc/passwd", "a/../../x"):
            with self.assertRaises(PermissionDenied):
                g.resolve(bad)

    def test_guard_blocks_symlink_escape(self):
        g = WorkspaceGuard(self.root / "ws")
        outside = self.root / "outside"
        outside.mkdir()
        (g.root / "link").symlink_to(outside)
        with self.assertRaises(PermissionDenied):
            g.resolve("link/file.txt")

    def test_default_deny_and_audit(self):
        audit = AuditLog(self.root / "audit.log")
        a = ApprovalManager(audit)
        self.assertFalse(a.request("delete", "x password=abc"))
        with self.assertRaises(PermissionDenied):
            a.require("delete", "x")
        entries = audit.tail()
        self.assertEqual(entries[0]["outcome"], "denied")
        self.assertNotIn("abc", entries[0]["detail"])

    def test_approver_exception_denies(self):
        def boom(a, d):
            raise RuntimeError("x")
        self.assertFalse(ApprovalManager(AuditLog(self.root / "a.log"), boom).request("a", "b"))

    def test_queue_approver(self):
        q = QueueApprover(timeout=5)
        result = []
        t = threading.Thread(target=lambda: result.append(q("run", "cmd")))
        t.start()
        for _ in range(100):
            if q.list_pending():
                break
            time.sleep(0.02)
        rid = q.list_pending()[0]["id"]
        self.assertTrue(q.decide(rid, True))
        t.join(5)
        self.assertEqual(result, [True])
        self.assertFalse(q.decide(rid, True))

    def test_queue_timeout_denies(self):
        self.assertFalse(QueueApprover(timeout=0.1)("a", "b"))

    def test_redact(self):
        self.assertNotIn("s3cr3t", redact("token = s3cr3t"))


if __name__ == "__main__":
    unittest.main()
