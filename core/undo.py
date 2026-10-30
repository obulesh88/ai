"""Undo stack for actions HEMA performed.

Each entry carries its own reversal callback, so nothing is guessed at undo time.
The callback returns a human-readable description of what it undid.
"""
import threading
from dataclasses import dataclass
from typing import Callable, List, Optional

from core.outcome import Result, failed, ok, unverified


@dataclass
class UndoEntry:
    label: str
    reverse: Callable[[], str]
    verify: Optional[Callable[[], bool]] = None


class UndoStack:
    def __init__(self, max_items: int = 25):
        self.max_items = max(1, max_items)
        self._entries: List[UndoEntry] = []
        self._lock = threading.Lock()

    def push(self, label: str, reverse: Callable[[], str],
             verify: Optional[Callable[[], bool]] = None) -> None:
        with self._lock:
            self._entries.append(UndoEntry(label, reverse, verify))
            if len(self._entries) > self.max_items:
                self._entries = self._entries[-self.max_items:]

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def can_undo(self) -> bool:
        with self._lock:
            return bool(self._entries)

    def peek(self) -> Optional[str]:
        with self._lock:
            return self._entries[-1].label if self._entries else None

    def history(self) -> List[str]:
        with self._lock:
            return [entry.label for entry in reversed(self._entries)]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def undo_last(self) -> Result:
        with self._lock:
            entry = self._entries.pop() if self._entries else None
        if entry is None:
            return failed("Nothing to undo")
        try:
            description = entry.reverse()
        except Exception as exc:  # a reversal must never crash the assistant
            return failed(f"Could not undo '{entry.label}': {type(exc).__name__}: {exc}")
        verified = True
        if entry.verify is not None:
            try:
                verified = bool(entry.verify())
            except Exception:
                verified = False
        if not verified:
            return unverified(
                f"Undid '{entry.label}' ({description}) but could not verify the result")
        return ok(f"Undid '{entry.label}' ({description})", {"label": entry.label})
