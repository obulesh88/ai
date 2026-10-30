"""Assistant identity: the names HEMA uses for itself and for you.

Mirrors the "assistant customisation" idea from other assistants: change the name
once and it applies to the greeting, the window title and the model's system prompt.
Persisted through interface.settings_store (data/settings.json).
"""
import re
from dataclasses import dataclass

MAX_NAME = 24
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class IdentityError(ValueError):
    """A name was empty, too long or contained control characters."""


def clean_name(value: str, field: str) -> str:
    name = " ".join(str(value or "").split())
    if not name:
        raise IdentityError(f"{field} cannot be empty")
    if len(name) > MAX_NAME:
        raise IdentityError(f"{field} must be at most {MAX_NAME} characters")
    if _CONTROL.search(name):
        raise IdentityError(f"{field} contains control characters")
    return name


@dataclass
class Identity:
    assistant_name: str = "HEMA"
    user_name: str = "Obuleswar"

    def __post_init__(self):
        self.assistant_name = clean_name(self.assistant_name, "assistant name")
        self.user_name = clean_name(self.user_name, "user name")

    def system_prompt(self) -> str:
        return (f"You are {self.assistant_name}, a helpful personal AI assistant running "
                f"locally on the user's computer. The user is {self.user_name}. "
                "Be concise, honest about what you have and have not verified, and never "
                "claim an action succeeded unless it did.")

    def greeting(self, hour: int = None) -> str:
        import time
        if hour is None:
            hour = time.localtime().tm_hour
        part = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
        return f"{part}, {self.user_name}. I'm {self.assistant_name}."

    def window_title(self) -> str:
        return f"{self.assistant_name} - Local AI Assistant"

    def to_dict(self) -> dict:
        return {"assistant_name": self.assistant_name, "user_name": self.user_name}

    @staticmethod
    def _safe(value, fallback: str) -> str:
        try:
            return clean_name(value, "name")
        except IdentityError:
            return fallback

    @classmethod
    def from_settings(cls, values: dict) -> "Identity":
        """Each field falls back independently, so one bad name keeps the other."""
        defaults = cls()
        values = values if isinstance(values, dict) else {}
        return cls(assistant_name=cls._safe(values.get("assistant_name"), defaults.assistant_name),
                   user_name=cls._safe(values.get("user_name"), defaults.user_name))
