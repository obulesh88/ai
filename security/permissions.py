"""Workspace restriction, approvals, audit log and secret protection."""
import json
import re
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional


class PermissionDenied(Exception):
    """An action was refused by the security layer."""


SECRET_RE = re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\b\s*[:=]\s*\S+")


def redact(text: str) -> str:
    return SECRET_RE.sub(lambda m: m.group(1) + "=[REDACTED]", text)


def contains_secret(text: str) -> bool:
    return bool(SECRET_RE.search(text))


class AuditLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, action: str, detail: str, outcome: str) -> None:
        entry = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "action": action,
                 "detail": redact(detail)[:500], "outcome": outcome}
        with self._lock, open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def tail(self, n: int = 50) -> List[dict]:
        if not self.path.is_file():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-n:]
        return [json.loads(x) for x in lines if x.strip()]


class WorkspaceGuard:
    """Only paths inside the root are allowed."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, path) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.root / p
        p = p.resolve()
        try:
            p.relative_to(self.root)
        except ValueError:
            raise PermissionDenied(f"Path is outside the approved workspace: {p}")
        return p


def deny_all(action: str, detail: str) -> bool:
    return False


def cli_approver(action: str, detail: str) -> bool:
    answer = input(f"\n[APPROVAL] {action}: {detail}\nAllow? (y/N) ").strip().lower()
    return answer in ("y", "yes")


class QueueApprover:
    """Used by the GUI: requests wait in a queue until the user decides (default deny on timeout)."""

    def __init__(self, timeout: float = 120.0):
        self.timeout = timeout
        self._lock = threading.Lock()
        self._next = 1
        self.pending: Dict[int, dict] = {}

    def __call__(self, action: str, detail: str) -> bool:
        with self._lock:
            rid = self._next
            self._next += 1
            item = {"id": rid, "action": action, "detail": detail,
                    "event": threading.Event(), "answer": False}
            self.pending[rid] = item
        item["event"].wait(self.timeout)
        with self._lock:
            self.pending.pop(rid, None)
        return item["answer"]

    def list_pending(self) -> List[dict]:
        with self._lock:
            return [{k: v[k] for k in ("id", "action", "detail")} for v in self.pending.values()]

    def decide(self, rid: int, allow: bool) -> bool:
        with self._lock:
            item = self.pending.get(rid)
        if not item:
            return False
        item["answer"] = bool(allow)
        item["event"].set()
        return True


class ApprovalManager:
    def __init__(self, audit: AuditLog, approver: Optional[Callable[[str, str], bool]] = None):
        self.audit = audit
        self.approver = approver or deny_all

    def request(self, action: str, detail: str) -> bool:
        try:
            ok = bool(self.approver(action, detail))
        except Exception as e:  # approver failure means deny
            self.audit.record(action, detail, f"denied (approver error: {e})")
            return False
        self.audit.record(action, detail, "approved" if ok else "denied")
        return ok

    def require(self, action: str, detail: str) -> None:
        if not self.request(action, detail):
            raise PermissionDenied(f"Not approved: {action}: {detail}")
