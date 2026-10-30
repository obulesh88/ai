"""File operations limited to the approved workspace, with backups before overwrite/delete."""
import shutil
import time
from pathlib import Path
from typing import List

from security.permissions import contains_secret


class BackupManager:
    def __init__(self, backups_dir):
        self.backups_dir = Path(backups_dir)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, path) -> Path:
        path = Path(path)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target = self.backups_dir / f"{path.name}.{stamp}.{time.time_ns() % 1000}.bak"
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)
        return target

    def restore(self, backup_path, original_path) -> None:
        backup_path, original_path = Path(backup_path), Path(original_path)
        if backup_path.is_dir():
            shutil.rmtree(original_path, ignore_errors=True)
            shutil.copytree(backup_path, original_path)
        else:
            shutil.copy2(backup_path, original_path)


class FileManager:
    def __init__(self, guard, approvals, backups: BackupManager):
        self.guard = guard
        self.approvals = approvals
        self.backups = backups

    def read(self, path) -> str:
        return self.guard.resolve(path).read_text(encoding="utf-8", errors="replace")

    def write(self, path, content: str, approve_overwrite: bool = True) -> Path:
        """New files are written directly. Existing files need approval and get a backup."""
        target = self.guard.resolve(path)
        if contains_secret(content):
            raise ValueError("Refusing to write a file that contains a password or API secret")
        if target.exists():
            if approve_overwrite:
                self.approvals.require("overwrite-file", str(target))
            self.backups.backup(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def delete(self, path) -> Path:
        target = self.guard.resolve(path)
        if not target.exists():
            raise FileNotFoundError(target)
        self.approvals.require("delete-file", str(target))
        backup = self.backups.backup(target)
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return backup

    def list(self, sub="") -> List[str]:
        base = self.guard.resolve(sub or ".")
        return sorted(str(p.relative_to(self.guard.root)) for p in base.iterdir())
