# HEMA - Local Personal AI Assistant

Status: **Segment 1 of 12 complete** (Ollama text chat). See JARVIS_PROGRESS_REPORT.md.

## Requirements
- Python 3.9+ (no extra packages needed for Segment 1)
- Ollama running locally (`ollama serve`) at http://127.0.0.1:11434

## Launch (Windows PowerShell)
```
cd path\to\project
copy .env.example .env   # optional; edit model/host
python main.py
```
Chat commands: `/models`, `/model <name>`, `/reset`, `/help`, `/quit`.
Default model: `qwen3-coder-local:latest` (falls back to the first installed model).

## Tests
```
python -m unittest discover -s . -t . -p "test_*.py" -v
```
Tests use a fake local Ollama server, so they do not need real Ollama.

## Layout (Segment 1)
- `config.py` settings / .env loader
- `ai/` Ollama client, model manager, prompt manager
- `core/` assistant and conversation context
- `tests/` automated tests

Other folders (voice, memory, automation, ...) will be added in their own segments.

## Verification status
- Verified (against a fake Ollama server only): model listing, streaming chat, context, error handling.
- NOT yet verified against your real Ollama: run `python main.py` on your PC.
