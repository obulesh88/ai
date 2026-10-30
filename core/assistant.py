"""HEMA assistant: text chat with conversation context."""
from typing import Iterator

from ai.model_manager import ModelManager
from ai.ollama_client import OllamaClient
from ai.prompt_manager import PromptManager
from config import Config
from core.conversation import Conversation


class Assistant:
    def __init__(self, config: Config, client: OllamaClient = None):
        self.config = config
        self.client = client or OllamaClient(config.ollama_host, config.timeout)
        self.models = ModelManager(self.client, config.default_model)
        self.prompts = PromptManager(config.system_prompt)
        self.conversation = Conversation(config.max_context_messages)

    def ask(self, text: str) -> Iterator[str]:
        """Stream a reply. History is only kept if the reply succeeds."""
        if self.models.current is None:
            self.models.auto_select()
        self.conversation.add("user", text)
        parts = []
        try:
            for chunk in self.client.chat_stream(
                self.models.current, self.prompts.build(self.conversation.messages)
            ):
                parts.append(chunk)
                yield chunk
        except Exception:
            self.conversation.drop_last()
            raise
        self.conversation.add("assistant", "".join(parts))
