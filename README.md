# HEMA - Local Personal AI Assistant

A modular, locally-run assistant. No paid APIs. Only the Python standard library is
required for the core; GUI, voice and charts are optional extras.

## Quick start (Windows PowerShell)
```
cd path\to\hema
python -m venv .venv
.venv\Scripts\activate            # optional but recommended
pip install -r requirements.txt   # core needs nothing extra
copy .env.example .env            # optional: edit model / host
ollama serve                      # in another window, if not already running
python main.py                    # text console
python main.py --gui              # desktop interface (needs: pip install PySide6)
```

## Tests
```
python -m unittest discover -s . -t . -p "test_*.py" -v
```
79 tests. They use a fake local Ollama server, so they run without Ollama.

## What works (verified)
| Area | Module | Verified by |
|---|---|---|
| Ollama text chat, streaming, model discovery | `ai/`, `core/assistant.py` | unit + integration tests |
| Conversation context, error handling | `core/conversation.py` | unit tests |
| SQLite memory (search/edit/delete, secret refusal) | `memory/` | unit tests |
| Permissions, approvals, audit log, workspace guard | `security/` | unit tests |
| Task planning, execution, retries, recovery | `core/task_manager.py`, `planner.py`, `executor.py` | unit tests |
| Files, commands, apps, processes, Windows startup | `automation/` | unit tests |
| Code inspection/editing/fixing | `coding/` | unit tests |
| Unity/Unreal/MCP project work | `game_development/` | unit tests (file level) |
| Self-update with backup + rollback | `core/self_update.py` | unit tests |
| Dragon Tiger statistics | `analytics/` | unit tests |
| Voice wake word + controller | `voice/` | unit tests (no real mic/TTS here) |
| End-to-end command routing | `core/hema.py`, `main.py` | integration + CLI run |

## NOT verified yet (needs your PC)
- Real Ollama and your models (`qwen3-coder-local:latest`, `qwen3.5:2b`)
- The PySide6 window (not installable in the sandbox)
- Real microphone, wake word and speech output
- Live Unity Editor and Unreal Editor actions (only file-level operations are tested)
- Real MCP servers (the probe works against a fake MCP server)

## Commands HEMA understands
```
/help /models /model <name> /reset /tasks /status /dt /quit
plan: <request>            show tasks            remember: <fact>
recall <text>              forget <id>            inspect: <path>
open <app>                 run: <command>         list processes
dragon|tiger|tie result    dragon tiger stats     run with windows
update yourself
```

## Safety
- All file access is restricted to `workspace/` (env `HEMA_WORKSPACE`).
- Overwrites, deletes, commands, app launches, microphone use and self-updates need approval.
- Destructive commands (format, net user, firewall/Defender changes, sudo/runas) are blocked outright.
- Every approval and denial is written to `logs/audit.log`.
- Passwords/API keys are refused by memory and file writes, and redacted from command output.

## Layout
```
core/ ai/ voice/ memory/ automation/ coding/ game_development/ analytics/ interface/ security/
tests/ data/ logs/ backups/ workspace/ main.py config.py requirements.txt .env.example
```

## Notes
- Unity Editor / Unreal Editor actions that need the running editor (creating GameObjects,
  Blueprints, verifying in-editor results) are NOT implemented through MCP yet: no MCP server
  is connected. `game_development/mcp_integration.py` detects configs and really handshakes a
  server when one is configured.
- Self-update applies code changes only when you pass explicit changes and approve them; it
  backs up first and rolls back if compile checks or tests fail.
