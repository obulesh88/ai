"""Persistent UI preferences (model choice etc.) stored as JSON in data/settings.json.

Only UI preferences live here. The Ollama URL stays in .env so we never silently
reconfigure the connection."""
import json
from pathlib import Path
from typing import Any, Dict

DEFAULTS: Dict[str, Any] = {"model": "", "ui_model": "qwen3.5:2b", "theme": "cyberpunk",
                            "timeout": 120, "assistant_name": "HEMA",
                            "user_name": "Obuleswar"}
ALLOWED = set(DEFAULTS)


def settings_path(data_dir) -> Path:
    return Path(data_dir) / "settings.json"


def load(data_dir) -> Dict[str, Any]:
    """Returns defaults merged with the saved file. Bad/corrupt files fall back to defaults."""
    values = dict(DEFAULTS)
    path = settings_path(data_dir)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return values
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key in ALLOWED and isinstance(value, (str, int, float, bool)):
                values[key] = value
    return values


def save(data_dir, values: Dict[str, Any]) -> Path:
    """Writes only known keys. Returns the path written."""
    path = settings_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    current = load(data_dir)
    for key, value in values.items():
        if key in ALLOWED:
            current[key] = value
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return path
