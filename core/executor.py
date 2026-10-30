"""Runs tasks through approved tools and verifies results."""
import time
from typing import Callable, Dict, Optional

from security.permissions import PermissionDenied


class TaskExecutor:
    def __init__(self, tasks, tools: Dict[str, Callable], verifier: Callable = None,
                 max_retries: int = 1):
        self.tasks = tasks
        self.tools = tools
        self.verifier = verifier
        self.max_retries = max_retries

    def run(self, task_id: int, action: Callable[[], object], tool_name: str = None) -> dict:
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"No task {task_id}")
        if task.status == "cancelled":
            return {"task": task_id, "status": "cancelled", "verified": False}
        if tool_name and tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' is not registered")
        self.tasks.set_status(task_id, "running")
        attempt, result, error = 0, None, None
        while attempt <= self.max_retries:
            current = self.tasks.get(task_id)
            if current and current.status == "cancelled":
                return {"task": task_id, "status": "cancelled", "verified": False}
            try:
                result = action()
                self.tasks.set_progress(task_id, 100)
                break
            except PermissionDenied as e:
                error = f"Not approved: {e}"
                self.tasks.add_error(task_id, error)
                self.tasks.set_status(task_id, "failed", report=error)
                return {"task": task_id, "status": "failed", "error": error}
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
                self.tasks.add_error(task_id, error)
                attempt += 1
                self.tasks._update(task_id, attempts=attempt)
                if attempt <= self.max_retries:
                    time.sleep(0.05)
        else:
            self.tasks.set_status(task_id, "failed", report=error or "failed")
            return {"task": task_id, "status": "failed", "error": error}

        verified = False
        note = ""
        if self.verifier:
            try:
                ok, note = self.verifier(result)
                verified = bool(ok)
            except Exception as e:
                note = f"Verification error: {e}"
        else:
            verified = True
            note = "No verifier configured; result returned without independent checks"
        self.tasks.set_status(task_id, "done", verified=verified,
                              report=f"{note} | result={result!r}"[:500])
        return {"task": task_id, "status": "done", "verified": verified,
                "result": result, "note": note}
