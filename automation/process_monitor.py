"""Lists processes without third-party packages."""
import subprocess
import sys
from typing import List


def list_processes(filter_text: str = "") -> List[str]:
    cmd = ["tasklist"] if sys.platform == "win32" else ["ps", "-eo", "pid,comm"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError) as e:
        return [f"Could not list processes: {e}"]
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if filter_text:
        lines = [ln for ln in lines if filter_text.lower() in ln.lower()]
    return lines[:200]


def is_running(name: str) -> bool:
    return any(name.lower() in ln.lower() for ln in list_processes())
