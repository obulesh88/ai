"""Builds the message list sent to the model."""
from typing import Dict, List


class PromptManager:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    def build(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return [{"role": "system", "content": self.system_prompt}] + list(history)
