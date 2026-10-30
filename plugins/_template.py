"""Copy this file to <name>.py (no leading underscore) and fill it in.

HEMA loads every *.py in plugins/ at startup. Files starting with "_" are ignored,
so this template never loads. A bad plugin is reported and skipped, never fatal.

Rules
- TOOL["name"] must be snake_case, at least 2 chars, and not a reserved word
  (run, command, undo, chat, help, exit, quit, system, python, plugin, memory, task).
- TOOL["description"] must be at least 10 characters: it tells HEMA when to use it.
- run(args, ctx) must return core.outcome.Result. Returning a string counts as
  "done"; returning None counts as "unverified".
- Plugins are ordinary Python running in-process with HEMA's permissions. Only put
  your own code here.
- Use ctx.files for any file access: it enforces the workspace boundary, takes a
  backup before overwriting, and records the action so "undo" works.
"""
from core.outcome import failed, ok

TOOL = {
    "name": "example",
    "description": "One or two sentences describing when HEMA should call this.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "text": {"type": "STRING", "description": "What the user wants"},
        },
        "required": ["text"],
    },
}


def run(args, ctx):
    text = str(args.get("text", "")).strip()
    if not text:
        return failed("nothing to work with")
    return ok(f"handled: {text}")
