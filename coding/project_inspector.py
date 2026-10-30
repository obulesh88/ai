"""Read-only inspection of a project folder."""
import ast
import json
from pathlib import Path
from typing import Dict, List

SKIP = {".git", "__pycache__", "node_modules", ".venv", "Library", "Temp", "Intermediate",
        "Binaries", "Saved", ".vs", "obj", "bin", "build"}


def detect_type(root) -> str:
    root = Path(root)
    if (root / "ProjectSettings" / "ProjectVersion.txt").is_file():
        return "unity"
    if list(root.glob("*.uproject")):
        return "unreal"
    if (root / "requirements.txt").is_file() or (root / "main.py").is_file():
        return "python"
    return "generic"


def tree(root, max_entries: int = 200) -> List[str]:
    root = Path(root).resolve()
    out = []
    for p in sorted(root.rglob("*")):
        if any(part in SKIP for part in p.relative_to(root).parts):
            continue
        out.append(str(p.relative_to(root)) + ("/" if p.is_dir() else ""))
        if len(out) >= max_entries:
            break
    return out


def inspect_project(root) -> Dict:
    root = Path(root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    files = [p for p in root.rglob("*") if p.is_file()
             and not any(part in SKIP for part in p.relative_to(root).parts)]
    ext: Dict[str, int] = {}
    for f in files:
        ext[f.suffix.lower() or "<none>"] = ext.get(f.suffix.lower() or "<none>", 0) + 1
    info = {"root": str(root), "type": detect_type(root), "file_count": len(files),
            "extensions": dict(sorted(ext.items(), key=lambda kv: -kv[1])[:10]),
            "entry_points": [n for n in ("main.py", "app.py", "setup.py") if (root / n).is_file()]}
    if info["type"] == "unity":
        from game_development.unity import UnityProject
        u = UnityProject(root)
        info["unity"] = {"version": u.editor_version(), "scenes": u.scenes()[:10]}
    if info["type"] == "unreal":
        from game_development.unreal import UnrealProject
        info["unreal"] = {"uproject": str(UnrealProject.find(root))}
    return info


def syntax_check_python(root) -> Dict[str, str]:
    """Return {file: error} for Python files that fail to compile."""
    errors = {}
    root = Path(root)
    for f in root.rglob("*.py"):
        if any(part in SKIP for part in f.relative_to(root).parts):
            continue
        try:
            ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
        except SyntaxError as e:
            errors[str(f.relative_to(root))] = f"line {e.lineno}: {e.msg}"
    return errors


def index_python_symbols(path) -> List[str]:
    """List top-level classes/functions so HEMA can understand a module."""
    tree_ = ast.parse(Path(path).read_text(encoding="utf-8", errors="replace"))
    names = []
    for node in tree_.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(f"{type(node).__name__.replace('Def','')} {node.name}")
    return names


def to_json(data) -> str:
    return json.dumps(data, indent=2)
