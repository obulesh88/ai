"""Self-maintenance: inspect source, propose, back up, apply with approval, test, roll back."""
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from coding.project_inspector import syntax_check_python
from security.permissions import PermissionDenied, WorkspaceGuard

PROTECTED_PREFIXES = ("security/",)


class SelfUpdater:
    def __init__(self, root, approvals, backups, python: str = None, tests_dir: str = "."):
        self.guard = WorkspaceGuard(root)
        self.root = self.guard.root
        self.approvals = approvals
        self.backups = backups
        self.python = python or sys.executable
        self.tests_dir = tests_dir

    def syntax_errors(self) -> Dict[str, str]:
        return syntax_check_python(self.root)

    def run_tests(self) -> tuple:
        proc = subprocess.run(
            [self.python, "-W", "ignore", "-m", "unittest", "discover",
             "-s", self.tests_dir, "-t", ".", "-p", "test_*.py"],
            cwd=str(self.root), capture_output=True, text=True, timeout=300)
        return proc.returncode == 0, (proc.stdout + proc.stderr)[-4000:]

    def inspect(self) -> dict:
        errors = self.syntax_errors()
        ok, output = self.run_tests() if not errors else (False, "Skipped: syntax errors")
        return {"syntax_errors": errors, "tests_ok": ok, "test_output": output}

    def propose(self, changes: Dict[str, str]) -> Dict[str, Path]:
        resolved = {}
        for rel, content in changes.items():
            resolved[str(self.guard.resolve(rel))] = content
        return resolved

    def apply(self, changes: Dict[str, str]) -> dict:
        """changes: {relative_path: new_content}. Returns a detailed result."""
        targets = {}
        for rel, content in changes.items():
            path = self.guard.resolve(rel)
            targets[path] = content
        if not targets:
            return {"ok": False, "error": "No changes proposed"}

        for path in targets:
            rel = str(path.relative_to(self.root)).replace("\\", "/")
            if any(rel.startswith(p) for p in PROTECTED_PREFIXES):
                self.approvals.require("security-change", f"Modify security code: {rel}")
        listing = ", ".join(sorted(str(p.relative_to(self.root)) for p in targets))
        self.approvals.require("self-update", f"Apply self-update to: {listing}")

        created: List[Path] = []
        backups: Dict[Path, Path] = {}
        for path, content in targets.items():
            if path.exists():
                backups[path] = self.backups.backup(path)
            else:
                created.append(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        errors = self.syntax_errors()
        result = {"ok": False, "applied": listing, "syntax_errors": errors}
        if errors:
            self._rollback(backups, created)
            result.update(rolled_back=True, reason="Syntax errors after update")
            return result

        tests_ok, output = self.run_tests()
        result.update(tests_ok=tests_ok, test_output=output)
        if not tests_ok:
            self._rollback(backups, created)
            result.update(rolled_back=True, reason="Tests failed after update")
            return result

        result.update(ok=True, rolled_back=False, reason="Update applied and tests passed")
        return result

    def _rollback(self, backups: Dict[Path, Path], created: List[Path]) -> None:
        for path, backup in backups.items():
            self.backups.restore(backup, path)
        for path in created:
            if path.exists():
                path.unlink()
