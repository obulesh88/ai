"""HEMA - local personal AI assistant.

Usage:
    python main.py          text console
    python main.py --gui    desktop interface (needs PySide6)
"""
import logging
import sys
from pathlib import Path

from ai.ollama_client import ModelNotFoundError, OllamaError
from config import load_config
from core.hema import Hema
from security.permissions import PermissionDenied, cli_approver

HELP = """Commands:
  /models              list installed Ollama models
  /model <name>        switch model
  /reset               clear conversation context
  /tasks               show tasks
  /status              show status
  /dt                  Dragon Tiger report
  /help                this help
  /quit                exit
Anything else is a natural-language command (see /help from HEMA)."""


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=log_dir / "hema.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")


def handle_slash(hema: Hema, line: str) -> bool:
    cmd, _, arg = line.partition(" ")
    arg = arg.strip()
    if cmd in ("/quit", "/exit"):
        return False
    if cmd == "/help":
        print(HELP)
    elif cmd == "/reset":
        hema.assistant.conversation.clear()
        print("Conversation cleared.")
    elif cmd == "/models":
        for m in hema.assistant.models.installed():
            print(("* " if m == hema.assistant.models.current else "  ") + m)
    elif cmd == "/model":
        print("Using model:", hema.assistant.models.select(arg))
    elif cmd == "/tasks":
        print(next(hema.handle("show tasks")))
    elif cmd == "/status":
        for k, v in hema.status().items():
            print(f"  {k}: {v}")
    elif cmd == "/dt":
        print(hema.dt.report_text())
    else:
        print("Unknown command." + HELP)
    return True


def run_cli(hema: Hema) -> int:
    config = hema.config
    print(f"HEMA console. Ollama: {config.ollama_host} | workspace: {hema.guard.root}")
    try:
        print("Model:", hema.assistant.models.auto_select())
    except OllamaError as e:
        print(f"Warning: {e}\nStart Ollama (ollama serve), then use /models or /model <name>.")
        logging.warning("Startup: %s", e)
    if hema.recovered:
        print(f"Recovered {len(hema.recovered)} unfinished task(s) from last session.")
    print("Type /help for commands.")
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
                if not handle_slash(hema, line):
                    break
                continue
            print("HEMA> ", end="", flush=True)
            for chunk in hema.handle(line):
                print(chunk, end="", flush=True)
            print()
        except (ModelNotFoundError, OllamaError) as e:
            print(f"\nOllama error: {e}")
            logging.error("Ollama error: %s", e)
        except PermissionDenied as e:
            print(f"\nNot permitted: {e}")
        except KeyboardInterrupt:
            print("\n(interrupted)")
    return 0


def run_gui() -> int:
    try:
        from interface.app import run_gui as start_gui
        from interface.controller import HemaController
        from security.permissions import QueueApprover
    except ImportError as e:
        print(f"GUI not available: {e}\nInstall it with: pip install PySide6")
        return 2
    approver = QueueApprover()
    hema = Hema(load_config(), approver)
    return start_gui(HemaController(hema))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    config = load_config()
    setup_logging(Path(config.logs_dir))
    if "--gui" in argv or "--desktop" in argv:
        return run_gui()
    hema = Hema(config, cli_approver)
    try:
        return run_cli(hema)
    finally:
        hema.close()


if __name__ == "__main__":
    sys.exit(main())
