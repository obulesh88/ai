"""HEMA configuration. Reads environment variables and an optional .env file."""
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Config:
    ollama_host: str
    default_model: str
    timeout: float
    max_context_messages: int
    system_prompt: str
    workspace_dir: Path = BASE_DIR / "workspace"
    data_dir: Path = BASE_DIR / "data"
    logs_dir: Path = BASE_DIR / "logs"
    backups_dir: Path = BASE_DIR / "backups"
    mcp_config: str = ""
    ui_model: str = "qwen3.5:2b"


def load_config() -> Config:
    _load_dotenv(BASE_DIR / ".env")
    return Config(
        ollama_host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/"),
        default_model=os.environ.get("HEMA_MODEL", "qwen3-coder-local:latest"),
        timeout=float(os.environ.get("HEMA_TIMEOUT", "120")),
        max_context_messages=int(os.environ.get("HEMA_MAX_CONTEXT", "20")),
        system_prompt=os.environ.get(
            "HEMA_SYSTEM_PROMPT",
            "You are HEMA, a helpful personal AI assistant running locally.",
        ),
        workspace_dir=Path(os.environ.get("HEMA_WORKSPACE", str(BASE_DIR / "workspace"))),
        mcp_config=os.environ.get("HEMA_MCP_CONFIG", ""),
        ui_model=os.environ.get("HEMA_UI_MODEL", "qwen3.5:2b"),
    )
