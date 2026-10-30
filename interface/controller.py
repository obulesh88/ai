"""Qt-free controller so the UI stays thin and testable."""
from typing import List, Optional

from core.hema import Hema


class HemaController:
    def __init__(self, hema: Hema):
        self.hema = hema
        self.log: List[str] = []

    def status_text(self) -> str:
        s = self.hema.status()
        return (f"Model: {s['model'] or 'not connected'}  |  Ollama: {s['ollama_host']}\n"
                f"Workspace: {s['workspace']}  |  Unfinished tasks: {s['unfinished_tasks']}")

    def models(self) -> List[str]:
        try:
            return self.hema.assistant.models.installed()
        except Exception as e:
            self.log.append(f"model list failed: {e}")
            return []

    def select_model(self, name: str) -> str:
        return self.hema.assistant.models.select(name)

    def ask(self, text: str):
        """Generator of response chunks; also records an activity log entry."""
        self.log.append(f"you: {text[:120]}")
        for chunk in self.hema.handle(text):
            yield chunk
        self.log.append("hema: replied")

    def tasks(self):
        return self.hema.tasks.list()

    def memories(self):
        return self.hema.memory.list()

    def delete_memory(self, mid: int) -> bool:
        self.hema.approvals.require("delete-memory", f"Memory #{mid}")
        return self.hema.memory.delete(mid)

    def pending_approvals(self) -> List[dict]:
        approver = self.hema.approvals.approver
        return approver.list_pending() if hasattr(approver, "list_pending") else []

    def decide_approval(self, rid: int, allow: bool) -> bool:
        approver = self.hema.approvals.approver
        return approver.decide(rid, allow) if hasattr(approver, "decide") else False

    def audit_tail(self, n: int = 50) -> List[dict]:
        return self.hema.audit.tail(n)

    def dt_report(self) -> str:
        return self.hema.dt.report_text()
