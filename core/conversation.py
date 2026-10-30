"""In-memory conversation context with a size limit."""
from typing import Dict, List


class Conversation:
    def __init__(self, max_messages: int = 20):
        self.max_messages = max(2, max_messages)
        self.messages: List[Dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def drop_last(self) -> None:
        if self.messages:
            self.messages.pop()

    def clear(self) -> None:
        self.messages = []
