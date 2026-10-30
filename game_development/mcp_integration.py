"""MCP awareness: reads server configs and probes a server with a real JSON-RPC handshake."""
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

HANDSHAKE = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                        "clientInfo": {"name": "hema", "version": "1.0"}}}


def load_servers(config_paths: List[str]) -> Dict[str, dict]:
    servers: Dict[str, dict] = {}
    for path in config_paths:
        p = Path(path)
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for name, cfg in (data.get("mcpServers") or {}).items():
            servers.setdefault(name, cfg)
    return servers


def describe(servers: Dict[str, dict]) -> List[dict]:
    out = []
    for name, cfg in servers.items():
        cmd = cfg.get("command", "")
        out.append({"name": name, "command": cmd, "configured": bool(cmd),
                    "command_found": bool(shutil.which(cmd)) if cmd else False,
                    "args": cfg.get("args", [])})
    return out


def probe(cfg: dict, timeout: float = 15.0) -> dict:
    """Start the server and send an MCP initialize request. Returns tool names if listed."""
    cmd = cfg.get("command")
    if not cmd or not shutil.which(cmd):
        return {"connected": False, "error": f"command not found: {cmd}"}
    argv = [cmd] + list(cfg.get("args", []))
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True)
    try:
        proc.stdin.write(json.dumps(HANDSHAKE) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        reply = json.loads(line) if line.strip() else {}
        connected = "result" in reply
        tools = []
        if connected:
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2,
                                         "method": "tools/list", "params": {}}) + "\n")
            proc.stdin.flush()
            tools_reply = json.loads(proc.stdout.readline() or "{}")
            tools = [t.get("name") for t in tools_reply.get("result", {}).get("tools", [])]
        return {"connected": connected, "tools": tools, "server_info": reply.get("result")}
    except (ValueError, OSError, subprocess.SubprocessError) as e:
        return {"connected": False, "error": str(e)}
    finally:
        proc.kill()
