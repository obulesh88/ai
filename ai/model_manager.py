"""Model discovery and selection."""
from typing import List, Optional

from ai.ollama_client import ModelNotFoundError, OllamaClient


class ModelManager:
    def __init__(self, client: OllamaClient, preferred: str):
        self.client = client
        self.preferred = preferred
        self.current: Optional[str] = None

    def installed(self) -> List[str]:
        return self.client.list_models()

    @staticmethod
    def _match(name: str, installed: List[str]) -> Optional[str]:
        if name in installed:
            return name
        if ":" not in name and name + ":latest" in installed:
            return name + ":latest"
        return None

    def select(self, name: str) -> str:
        installed = self.installed()
        found = self._match(name, installed)
        if not found:
            raise ModelNotFoundError(
                f"Model '{name}' is not installed. Installed: {', '.join(installed) or 'none'}"
            )
        self.current = found
        return found

    def auto_select(self) -> str:
        """Use the preferred model; otherwise fall back to the first installed one."""
        installed = self.installed()
        found = self._match(self.preferred, installed)
        if not found:
            if not installed:
                raise ModelNotFoundError("No models installed in Ollama.")
            found = installed[0]
        self.current = found
        return found
