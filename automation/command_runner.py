"""Runs approved commands only. Blocks obviously destructive command lines."""
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from security.permissions import PermissionDenied, redact

BLOCKED = (
    "format ", "diskpart", "bcdedit", "reg delete", "takeown", "icacls ",
    "cipher /w", "vssadmin delete", "shutdown ", "net user ", "del /f /s /q c:",
    "rmdir /s /q c:", "rm -rf /", ":(){ :|:& };:", "set-mppreference",
    "netsh advfirewall set", "disableantispyware", "-disablerealtimemonitoring",
    "runas ", "sudo ", "start-process -verb runas",
)


class CommandRunner:
    def __init__(self, approvals, guard, timeout: float = 120.0):
        self.approvals = approvals
        self.guard = guard
        self.timeout = timeout

    def check_allowed(self, command: str) -> None:
        low = " ".join(command.lower().split())
        for bad in BLOCKED:
            if bad in low:
                raise PermissionDenied(f"Command contains a blocked operation: {bad.strip()}")

    def run(self, command: str, cwd=None) -> Tuple[int, str]:
        """Returns (exit_code, combined_output). Requires explicit approval."""
        self.check_allowed(command)
        workdir = str(self.guard.resolve(cwd or "."))
        self.approvals.require("run-command", f"{command} (in {workdir})")
        proc = subprocess.run(command, shell=True, cwd=workdir, capture_output=True,
                              text=True, timeout=self.timeout)
        out = redact((proc.stdout or "") + (proc.stderr or ""))
        return proc.returncode, out[-4000:]

    @staticmethod
    def python() -> str:
        return shlex.quote(sys.executable) if sys.platform != "win32" else f'"{sys.executable}"'
