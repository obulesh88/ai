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

    def use_model(self, name: str) -> str:
        """Switches the session model without a network call; name must come from models()."""
        self.hema.assistant.models.current = name
        return name

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

    def delete_memory_confirmed(self, mid: int) -> bool:
        """Used by the GUI after the user confirms in a modal dialog (avoids thread deadlock).

        The confirmation is still written to the audit log.
        """
        self.hema.audit.record("delete-memory", f"Memory #{mid}", "approved (GUI confirmation)")
        return self.hema.memory.delete(mid)

    def workspace_path(self) -> str:
        return str(self.hema.guard.root)

    def identity(self):
        return self.hema.identity

    def set_identity(self, assistant_name: str = None, user_name: str = None):
        return self.hema.set_identity(assistant_name, user_name)

    def ollama_host(self) -> str:
        return self.hema.config.ollama_host

    def ui_model(self) -> str:
        return getattr(self.hema.config, "ui_model", "qwen3.5:2b")

    def mcp_servers(self):
        from game_development.mcp_integration import describe, load_servers
        cfg = getattr(self.hema.config, "mcp_config", "")
        return describe(load_servers([cfg] if cfg else []))

    def known_commands(self):
        from core.command_router import PATTERNS
        return [(kind, pattern) for kind, pattern in PATTERNS]

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
