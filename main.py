"""HEMA - Segment 1: text chat with a local Ollama model."""
import logging
import sys
from pathlib import Path

from ai.ollama_client import ModelNotFoundError, OllamaError
from config import BASE_DIR, load_config
from core.assistant import Assistant

HELP = "Commands: /models  /model <name>  /reset  /help  /quit"


def setup_logging() -> None:
    log_dir = Path(BASE_DIR) / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "hema.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def handle_command(assistant: Assistant, line: str) -> bool:
    """Return False to quit."""
    cmd, _, arg = line.partition(" ")
    if cmd == "/quit":
        return False
    if cmd == "/help":
        print(HELP)
    elif cmd == "/reset":
        assistant.conversation.clear()
        print("Conversation cleared.")
    elif cmd == "/models":
        models = assistant.models.installed()
        for m in models:
            print(("* " if m == assistant.models.current else "  ") + m)
        if not models:
            print("No models installed.")
    elif cmd == "/model":
        if not arg.strip():
            print("Usage: /model <name>")
        else:
            print("Using model:", assistant.models.select(arg.strip()))
    else:
        print("Unknown command. " + HELP)
    return True


def main() -> int:
    setup_logging()
    config = load_config()
    assistant = Assistant(config)
    print(f"HEMA text chat. Ollama: {config.ollama_host}")
    try:
        print("Model:", assistant.models.auto_select())
    except OllamaError as e:
        print(f"Warning: {e}\nStart Ollama (ollama serve) and use /models or /model <name>.")
        logging.warning("Startup: %s", e)
    print(HELP)
    while True:
        try:
            line = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        try:
            if line.startswith("/"):
                if not handle_command(assistant, line):
                    break
                continue
            print("HEMA> ", end="", flush=True)
            for chunk in assistant.ask(line):
                print(chunk, end="", flush=True)
            print()
        except ModelNotFoundError as e:
            print(f"\nModel error: {e}")
            logging.error("Model error: %s", e)
        except OllamaError as e:
            print(f"\nOllama error: {e}")
            logging.error("Ollama error: %s", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
