"""HEMA note plugin: append a timestamped note to workspace/notes.md.

Demonstrates the plugin contract: declare TOOL, define run(args, ctx), return a
Result. Writes go through ctx.files, so they are workspace-guarded, backed up and
listed as undoable actions.
"""
import time

from core.outcome import failed, ok, unverified

TOOL = {
    "name": "note",
    "description": ("Append a timestamped note to notes.md in the workspace. Use when the "
                    "user says 'note this', 'write that down' or 'add to my notes'."),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "text": {"type": "STRING", "description": "The note to append"},
        },
        "required": ["text"],
    },
}

NOTES_FILE = "notes.md"


def run(args, ctx):
    text = " ".join(str(args.get("text", "")).split())
    if not text:
        return failed("note needs some text")
    if ctx.files is None:
        return failed("this plugin needs a file manager")
    line = f"- {time.strftime('%Y-%m-%d %H:%M')}  {text}\n"
    try:
        exists = ctx.resolve(NOTES_FILE).exists()
        previous = ctx.files.read(NOTES_FILE) if exists else "# HEMA notes\n\n"
        path = ctx.files.write(NOTES_FILE, previous + line)
    except Exception as exc:
        return failed(f"could not write notes: {type(exc).__name__}: {exc}")
    if not path.exists():
        return unverified(f"wrote {path} but it is not readable")
    return ok(f"noted to {NOTES_FILE}", {"path": str(path), "text": text})
