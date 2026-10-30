"""Explicit outcome reporting.

Every action built after this file returns a Result, so nothing is reported as a
success unless it was actually verified. Idea: "done / unverified / failed".
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class Outcome(str, Enum):
    DONE = "done"
    UNVERIFIED = "unverified"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value


@dataclass
class Result:
    outcome: Outcome
    detail: str
    data: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.outcome is Outcome.DONE

    def speak(self) -> str:
        """One line suitable for chat or speech."""
        return f"[{self.outcome.value}] {self.detail}"

    def __str__(self) -> str:
        return self.speak()


def ok(detail: str, data: Dict[str, Any] = None) -> Result:
    return Result(Outcome.DONE, detail, data)


def unverified(detail: str, data: Dict[str, Any] = None) -> Result:
    return Result(Outcome.UNVERIFIED, detail, data)


def failed(detail: str, data: Dict[str, Any] = None) -> Result:
    return Result(Outcome.FAILED, detail, data)
