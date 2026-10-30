"""Task storage with progress recovery, retries and verification status."""
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

STATUSES = ("pending", "running", "done", "failed", "cancelled")


class Task:
    def __init__(self, row: Dict):
        self.__dict__.update(row)

    def __repr__(self):
        return f"<Task {self.id} {self.status} {self.description[:40]!r}>"


class TaskManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.executescript(
                """CREATE TABLE IF NOT EXISTS tasks(
                   id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL,
                   priority INTEGER NOT NULL DEFAULT 3, status TEXT NOT NULL DEFAULT 'pending',
                   plan TEXT NOT NULL DEFAULT '[]', tools TEXT NOT NULL DEFAULT '[]',
                   progress INTEGER NOT NULL DEFAULT 0, errors TEXT NOT NULL DEFAULT '[]',
                   attempts INTEGER NOT NULL DEFAULT 0, report TEXT NOT NULL DEFAULT '',
                   verified INTEGER NOT NULL DEFAULT 0,
                   created REAL, updated REAL);""")
            self.conn.commit()

    def _exec(self, sql, args=()):
        with self._lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur

    def create(self, description: str, plan: List[str] = None, tools: List[str] = None,
               priority: int = 3) -> int:
        if not description.strip():
            raise ValueError("Task description is empty")
        now = time.time()
        return self._exec(
            "INSERT INTO tasks(description,priority,plan,tools,created,updated) VALUES(?,?,?,?,?,?)",
            (description.strip(), max(1, min(5, priority)), json.dumps(plan or []),
             json.dumps(tools or []), now, now)).lastrowid

    def _update(self, task_id: int, **fields) -> None:
        if not fields:
            return
        fields["updated"] = time.time()
        sets = ", ".join(f"{k}=?" for k in fields)
        self._exec(f"UPDATE tasks SET {sets} WHERE id=?", tuple(fields.values()) + (task_id,))

    def get(self, task_id: int) -> Optional[Task]:
        row = self._exec("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return Task(dict(row)) if row else None

    def list(self, status: str = None) -> List[Task]:
        if status:
            rows = self._exec("SELECT * FROM tasks WHERE status=? ORDER BY priority,id", (status,))
        else:
            rows = self._exec("SELECT * FROM tasks ORDER BY id")
        return [Task(dict(r)) for r in rows.fetchall()]

    def set_status(self, task_id: int, status: str, verified: bool = False, report: str = "") -> None:
        if status not in STATUSES:
            raise ValueError(f"Unknown status {status}")
        fields = {"status": status, "verified": int(bool(verified)), "report": report}
        if status == "done":
            fields["progress"] = 100
        self._update(task_id, **fields)

    def set_progress(self, task_id: int, percent: int) -> None:
        self._update(task_id, progress=max(0, min(100, int(percent))))

    def add_error(self, task_id: int, error: str) -> None:
        task = self.get(task_id)
        errors = json.loads(task.errors) if task else []
        errors.append(error[:500])
        self._update(task_id, errors=json.dumps(errors))

    def cancel(self, task_id: int) -> None:
        self.set_status(task_id, "cancelled")

    def unfinished(self) -> List[Task]:
        rows = self._exec("SELECT * FROM tasks WHERE status IN ('pending','running') ORDER BY id")
        return [Task(dict(r)) for r in rows.fetchall()]

    def recover(self) -> List[Task]:
        """After a restart, mark crashed 'running' tasks back to pending so they can retry."""
        for t in self.unfinished():
            if t.status == "running":
                self._update(t.id, status="pending")
                self.add_error(t.id, "Previous run was interrupted; reset to pending for retry")
        return self.unfinished()

    def close(self) -> None:
        with self._lock:
            self.conn.close()
