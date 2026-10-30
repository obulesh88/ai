"""SQLite persistent memory: conversation history and approved memories."""
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List

from security.permissions import contains_secret

KINDS = ("preference", "project", "path", "task", "feature", "error", "note")


class MemoryManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.executescript(
                """CREATE TABLE IF NOT EXISTS memories(
                       id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
                       content TEXT NOT NULL, created REAL NOT NULL);
                   CREATE TABLE IF NOT EXISTS messages(
                       id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL,
                       content TEXT NOT NULL, created REAL NOT NULL);""")
            self.conn.commit()

    def _exec(self, sql, args=()):
        with self._lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur

    def add(self, kind: str, content: str) -> int:
        if kind not in KINDS:
            raise ValueError(f"Unknown memory kind '{kind}'. Use one of {KINDS}")
        if not content.strip():
            raise ValueError("Memory content is empty")
        if contains_secret(content):
            raise ValueError("Refusing to store text that looks like a password or API secret")
        return self._exec("INSERT INTO memories(kind,content,created) VALUES(?,?,?)",
                          (kind, content.strip(), time.time())).lastrowid

    def list(self, kind: str = None) -> List[Dict]:
        if kind:
            rows = self._exec("SELECT * FROM memories WHERE kind=? ORDER BY id", (kind,))
        else:
            rows = self._exec("SELECT * FROM memories ORDER BY id")
        return [dict(r) for r in rows.fetchall()]

    def search(self, text: str) -> List[Dict]:
        like = "%" + text.replace("%", "\\%").replace("_", "\\_") + "%"
        rows = self._exec("SELECT * FROM memories WHERE content LIKE ? ESCAPE '\\' ORDER BY id", (like,))
        return [dict(r) for r in rows.fetchall()]

    def update(self, memory_id: int, content: str) -> bool:
        if contains_secret(content):
            raise ValueError("Refusing to store text that looks like a password or API secret")
        return self._exec("UPDATE memories SET content=? WHERE id=?", (content.strip(), memory_id)).rowcount > 0

    def delete(self, memory_id: int) -> bool:
        return self._exec("DELETE FROM memories WHERE id=?", (memory_id,)).rowcount > 0

    def add_message(self, role: str, content: str) -> None:
        if contains_secret(content):
            content = "[message not stored: looked like it contained a secret]"
        self._exec("INSERT INTO messages(role,content,created) VALUES(?,?,?)", (role, content, time.time()))

    def recent_messages(self, limit: int = 20) -> List[Dict]:
        rows = self._exec("SELECT role,content FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in reversed(rows)]

    def clear_messages(self) -> None:
        self._exec("DELETE FROM messages")

    def close(self) -> None:
        with self._lock:
            self.conn.close()
