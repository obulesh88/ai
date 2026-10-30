"""Turns natural language into an intent. Rules are explicit; unknown input goes to chat."""
import re
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Intent:
    kind: str
    args: Dict[str, str] = field(default_factory=dict)
    raw: str = ""


PATTERNS = (
    ("self_update", r"^(hey hema[, ]*)?(update yourself|update hema|self[- ]update)\b"),
    ("plan", r"^(hey hema[, ]*)?plan\s*[:\-]?\s*(.+)$"),
    ("tasks", r"^(hey hema[, ]*)?(show|list)\s+(my\s+)?tasks?$"),
    ("remember", r"^(hey hema[, ]*)?remember( that)?[:\s]+(.+)$"),
    ("recall", r"^(hey hema[, ]*)?(recall|search memory for)\s+(.+)$"),
    ("forget", r"^(hey hema[, ]*)?forget( memory)?\s+(\d+)$"),
    ("inspect", r"^(hey hema[, ]*)?inspect( project)?[:\s]+(.+)$"),
    ("open_app", r"^(hey hema[, ]*)?(open|launch|start)\s+([\w .-]+)$"),
    ("undo_history", r"^(hey hema[, ]*)?(what can you undo|undo history|undo list)$"),
    ("undo", r"^(hey hema[, ]*)?undo( last)?$"),
    ("plugin_list", r"^(hey hema[, ]*)?(list|show)( me)?( the)? plugins$"),
    ("plugin_run", r"^(hey hema[, ]*)?(?:run|use|execute)\s+plugin\s+([a-z0-9_]+)\s*(.*)$"),
    ("run_command", r"^(hey hema[, ]*)?run( command)?[:\s]+(.+)$"),
    ("processes", r"^(hey hema[, ]*)?(list processes|processes)\s*(.*)$"),
    ("dt_record", r"^(hey hema[, ]*)?(dragon|tiger|tie)\s+result$"),
    ("dt_stats", r"^(hey hema[, ]*)?dragon\s*tiger\s*(stats|statistics|report)$"),
    ("startup_install", r"^(hey hema[, ]*)?(start|run)\s+(with|at)\s+windows$"),
    ("help", r"^(hey hema[, ]*)?help$"),
)

COMPILED = [(k, re.compile(p, re.I)) for k, p in PATTERNS]


def route(text: str) -> Intent:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return Intent("empty", raw=text)
    for kind, regex in COMPILED:
        m = regex.match(cleaned)
        if not m:
            continue
        groups = [g for g in m.groups()[1:] if g is not None]
        if kind == "remember":
            return Intent(kind, {"content": groups[-1].strip()}, cleaned)
        if kind == "forget":
            return Intent(kind, {"id": groups[-1]}, cleaned)
        if kind in ("recall", "inspect", "run_command"):
            return Intent(kind, {"text": groups[-1].strip()}, cleaned)
        if kind == "plugin_run":
            rest = (groups[1] if len(groups) > 1 else "").strip()
            return Intent(kind, {"name": groups[0], "args": rest}, cleaned)
        if kind == "plan":
            return Intent(kind, {"request": groups[-1].strip()}, cleaned)
        if kind == "open_app":
            return Intent(kind, {"app": groups[-1].strip()}, cleaned)
        if kind == "processes":
            return Intent(kind, {"filter": (groups[-1] if groups else "").strip()}, cleaned)
        if kind == "dt_record":
            return Intent(kind, {"outcome": groups[-1].lower()}, cleaned)
        return Intent(kind, {}, cleaned)
    return Intent("chat", {"text": cleaned}, cleaned)
