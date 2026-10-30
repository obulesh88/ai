"""Windows autostart: writes a .bat launcher into the user's Startup folder (needs approval)."""
import sys
from pathlib import Path


def startup_dir() -> Path:
    return (Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" /
            "Start Menu" / "Programs" / "Startup")


def startup_script(project_root) -> str:
    python = str(Path(sys.executable))
    root = Path(project_root)
    return (
        "@echo off\r\n"
        f'cd /d "{root}"\r\n'
        f'"{python}" main.py --gui >> "{root}\\logs\\startup.log" 2>&1\r\n'
    )


def install_startup(project_root, approvals, target_dir: Path = None) -> Path:
    target_dir = Path(target_dir) if target_dir else startup_dir()
    approvals.require("install-startup", f"Create HEMA launcher in {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    script = target_dir / "HEMA.bat"
    script.write_text(startup_script(project_root), encoding="utf-8")
    return script


def remove_startup(approvals, target_dir: Path = None) -> bool:
    target_dir = Path(target_dir) if target_dir else startup_dir()
    script = target_dir / "HEMA.bat"
    if not script.exists():
        return False
    approvals.require("remove-startup", f"Delete {script}")
    script.unlink()
    return True
