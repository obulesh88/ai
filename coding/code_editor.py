"""Creates and edits code files safely (backup + approval for existing files)."""
from pathlib import Path


class CodeEditor:
    def __init__(self, files):
        self.files = files

    def create(self, path, content: str) -> Path:
        return self.files.write(path, content)

    def replace(self, path, old: str, new: str) -> Path:
        """Replace exactly one occurrence; refuses ambiguous or missing matches."""
        text = self.files.read(path)
        count = text.count(old)
        if count == 0:
            raise ValueError(f"Text to replace was not found in {path}")
        if count > 1:
            raise ValueError(f"Text occurs {count} times in {path}; refusing an ambiguous edit")
        return self.files.write(path, text.replace(old, new, 1))

    def append(self, path, text: str) -> Path:
        current = self.files.read(path)
        return self.files.write(path, current + text)
