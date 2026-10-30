"""Unity project integration (files are real; Editor verification needs the Editor running)."""
import re
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_TEMPLATE = '''using UnityEngine;

public class {class_name} : MonoBehaviour
{{
    // Created by HEMA
{body}
}}
'''

ERROR_RE = re.compile(r"(error CS\d+:[^\n]*)")


class UnityProject:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not self.is_unity_project():
            raise ValueError(f"Not a Unity project: {self.root}")

    def is_unity_project(self) -> bool:
        return (self.root / "ProjectSettings" / "ProjectVersion.txt").is_file()

    def editor_version(self) -> str:
        text = (self.root / "ProjectSettings" / "ProjectVersion.txt").read_text(encoding="utf-8")
        m = re.search(r"m_EditorVersion:\s*(\S+)", text)
        return m.group(1) if m else "unknown"

    def scenes(self) -> List[str]:
        return sorted(str(p.relative_to(self.root)) for p in self.root.glob("Assets/**/*.unity"))

    def scripts(self) -> List[str]:
        return sorted(str(p.relative_to(self.root)) for p in self.root.glob("Assets/**/*.cs"))

    def scene_objects(self, scene_path) -> List[str]:
        """Best-effort read of GameObject names from a scene's YAML."""
        p = self.root / scene_path
        text = p.read_text(encoding="utf-8", errors="replace")
        names = re.findall(r"^  m_Name: (.+)$", text, re.M)
        return [n for n in names if n.strip()]

    def create_script(self, name: str, body: str = "void Start() { }", folder: str = "Assets/Scripts") -> Path:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid C# class name: {name}")
        target = self.root / folder / f"{name}.cs"
        content = SCRIPT_TEMPLATE.format(class_name=name, body="    " + body.strip())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    @staticmethod
    def parse_console_errors(log_text: str) -> List[str]:
        return ERROR_RE.findall(log_text)[:50]

    def read_editor_log(self, log_path=None) -> str:
        """Editor.log lives outside the workspace on Windows; the caller must approve this read."""
        p = Path(log_path) if log_path else (
            Path.home() / "AppData" / "Local" / "Unity" / "Editor" / "Editor.log")
        if not p.is_file():
            return ""
        text = p.read_text(encoding="utf-8", errors="replace")
        return text[-200000:]
