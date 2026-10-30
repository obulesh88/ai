"""Asks the local model for code, then writes it safely and checks syntax."""
import re
from typing import Optional

from coding.project_inspector import syntax_check_python

CODE_PROMPT = (
    "You are a careful Python developer. Reply with ONE fenced code block containing the "
    "complete file and nothing else. No explanations."
)


def extract_code(text: str) -> Optional[str]:
    blocks = re.findall(r"```(?:python|py|cs|cpp|h)?\n(.*?)```", text, re.S)
    if blocks:
        return max(blocks, key=len)
    return text.strip() if text.strip() else None


class CodeAgent:
    def __init__(self, chat, editor, guard_root):
        self.chat = chat
        self.editor = editor
        self.root = guard_root
        self.backups = editor.files.backups

    def generate_file(self, path: str, request: str) -> dict:
        reply = self.chat([{"role": "system", "content": CODE_PROMPT},
                           {"role": "user", "content": request}])
        code = extract_code(reply)
        if not code:
            return {"ok": False, "error": "Model returned no code"}
        target = self.editor.create(path, code)
        result = {"ok": True, "path": str(target)}
        if target.suffix == ".py":
            errors = syntax_check_python(target.parent)
            rel = str(target.relative_to(self.root)) if str(target).startswith(str(self.root)) else target.name
            result["syntax_error"] = errors.get(rel)
            if result["syntax_error"]:
                result["ok"] = False
        return result

    def fix_syntax_error(self, path: str, attempts: int = 1) -> dict:
        """Ask the model to rewrite a file that fails to compile; keeps a backup each time."""
        from pathlib import Path
        from coding.project_inspector import syntax_check_python as check
        path = Path(path)
        for i in range(attempts + 1):
            errors = check(path.parent)
            if not errors:
                return {"ok": True, "attempts": i}
            err_text = "; ".join(f"{k}: {v}" for k, v in errors.items())
            reply = self.chat([
                {"role": "system", "content": CODE_PROMPT},
                {"role": "user", "content": f"Fix this Python file. Error: {err_text}\n\n"
                                            f"File {path.name}:\n{path.read_text(errors='replace')}"}])
            code = extract_code(reply)
            if not code:
                break
            self.editor.files.write(path, code)
        remaining = check(path.parent)
        return {"ok": not remaining, "attempts": attempts, "errors": remaining}
