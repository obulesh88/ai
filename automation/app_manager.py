"""Opens only explicitly approved applications."""
import subprocess
import sys
from pathlib import Path

from security.permissions import PermissionDenied

DEFAULT_ALLOWED = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "explorer": "explorer.exe",
    "vscode": "code",
    "unity": "Unity.exe",
    "unreal": "UnrealEditor.exe",
}


class AppManager:
    def __init__(self, approvals, allowed: dict = None):
        self.approvals = approvals
        self.allowed = dict(DEFAULT_ALLOWED)
        self.allowed.update(allowed or {})

    def allow(self, name: str, target: str) -> None:
        self.allowed[name.lower()] = target

    def launch(self, name: str) -> str:
        key = name.strip().lower()
        if key not in self.allowed:
            raise PermissionDenied(
                f"'{name}' is not in the approved app list: {sorted(self.allowed)}")
        target = self.allowed[key]
        self.approvals.require("launch-app", f"{key} -> {target}")
        if sys.platform == "win32":
            subprocess.Popen(f'start "" "{target}"', shell=True)
        else:
            subprocess.Popen([target.replace(".exe", "")] if Path(target).suffix == ".exe" else [target])
        return target
