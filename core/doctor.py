"""Environment self-check used by `python main.py --doctor`."""
import importlib
import json
import shutil
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from ai.ollama_client import OllamaClient, OllamaError

OPTIONAL = (
    ("PySide6", "desktop interface (python main.py --gui)"),
    ("pyttsx3", "offline speech output"),
    ("speech_recognition", "microphone speech-to-text"),
    ("matplotlib", "Dragon Tiger charts"),
)


def _writable(path: Path) -> tuple:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".hema_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True, "writable"
    except OSError as e:
        return False, str(e)


def run_checks(config, client: OllamaClient = None) -> list:
    """Returns a list of (name, ok, detail) tuples."""
    checks = []
    checks.append(("Python", sys.version_info >= (3, 9), f"{sys.version.split()[0]} at {sys.executable}"))

    client = client or OllamaClient(config.ollama_host, min(config.timeout, 10))
    host = urlparse(client.host)
    port = host.port or (443 if host.scheme == "https" else 80)
    try:
        socket.create_connection((host.hostname, port), timeout=3).close()
        reachable, detail = True, f"port {port} open on {host.hostname}"
    except OSError as e:
        reachable, detail = False, f"cannot connect to {host.hostname}:{port} ({e})"
    checks.append(("Ollama port", reachable, detail))

    if reachable:
        try:
            version = json.loads(urlopen(client.host + "/api/version", timeout=5).read()).get("version", "?")
            checks.append(("Ollama API", True, f"version {version}"))
        except Exception as e:
            checks.append(("Ollama API", False, f"/api/version failed: {e}"))
        try:
            models = client.list_models()
            ok = bool(models)
            note = ", ".join(models) if models else "no models installed - run: ollama pull <model>"
            checks.append(("Ollama models", ok, note))
            checks.append(("Preferred model", config.default_model in models or
                           config.default_model + ":latest" in models,
                           f"{config.default_model} " +
                           ("installed" if (config.default_model in models or config.default_model + ":latest" in models)
                            else f"NOT found (installed: {', '.join(models) or 'none'})")))
        except OllamaError as e:
            checks.append(("Ollama models", False, str(e)))

    for label, path in (("workspace", Path(config.workspace_dir)), ("data", Path(config.data_dir)),
                        ("logs", Path(config.logs_dir)), ("backups", Path(config.backups_dir))):
        ok, detail = _writable(path)
        checks.append((f"Folder {label}", ok, f"{path} - {detail}"))

    free_gb = shutil.disk_usage(str(Path(config.data_dir).parent)).free / 1e9
    checks.append(("Disk space", free_gb > 1, f"{free_gb:.1f} GB free"))

    for module, purpose in OPTIONAL:
        try:
            importlib.import_module(module)
            checks.append((f"Optional: {module}", True, purpose))
        except ImportError:
            checks.append((f"Optional: {module}", None, f"not installed - needed for {purpose}"))
    return checks


def format_report(checks: list) -> str:
    lines = []
    for name, ok, detail in checks:
        mark = "OK  " if ok is True else ("FAIL" if ok is False else "--  ")
        lines.append(f"[{mark}] {name:22s} {detail}")
    failures = [c for c in checks if c[1] is False]
    lines.append("")
    lines.append("All critical checks passed." if not failures
                 else f"{len(failures)} problem(s) found: " + ", ".join(c[0] for c in failures))
    return "\n".join(lines)
