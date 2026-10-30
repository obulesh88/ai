"""Drop-in skill plugins.

A plugin is one .py file in plugins/ that declares TOOL and defines run(args, ctx).

    TOOL = {"name": "note", "description": "...", "parameters": {...}}
    def run(args: dict, ctx) -> Result

Plugins are ordinary Python running in-process with HEMA's permissions, so only
your own files belong in plugins/. Anything invalid is reported and skipped: a
broken plugin can never stop the assistant from starting.
"""
import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.outcome import Result, failed, ok, unverified

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
RESERVED = {"run", "command", "undo", "chat", "help", "exit", "quit", "system",
            "python", "plugin", "memory", "task"}


class PluginError(Exception):
    """A plugin file could not be used."""


@dataclass
class Plugin:
    name: str
    description: str
    parameters: Dict[str, Any]
    run: Callable[..., Any]
    path: Path

    def describe(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description,
                "parameters": self.parameters, "file": self.path.name}


@dataclass
class PluginContext:
    """What a plugin is allowed to reach."""
    root: Path
    files: Any = None          # automation.file_manager.FileManager
    memory: Any = None         # memory.memory_manager.MemoryManager

    def resolve(self, relative: str) -> Path:
        return Path(self.root) / relative


def load_plugin_file(path: Path) -> Plugin:
    path = Path(path)
    if path.suffix != ".py" or path.name.startswith("_"):
        raise PluginError("not a plugin file")
    module_name = "hema_plugin_" + path.stem
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise PluginError("cannot be imported")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:
        raise PluginError(f"{type(exc).__name__}: {exc}") from exc

    tool = getattr(module, "TOOL", None)
    runner = getattr(module, "run", None)
    if not isinstance(tool, dict):
        raise PluginError("missing TOOL dict")
    if not callable(runner):
        raise PluginError("missing run(args, ctx)")
    name = str(tool.get("name", "")).strip()
    if not NAME_RE.match(name):
        raise PluginError(f"invalid tool name {name!r} (use snake_case)")
    description = str(tool.get("description", "")).strip()
    if len(description) < 10:
        raise PluginError("TOOL needs a description that says when to use it")
    parameters = tool.get("parameters") or {"type": "OBJECT", "properties": {}}
    if not isinstance(parameters, dict):
        raise PluginError("TOOL['parameters'] must be a dict")
    return Plugin(name=name, description=description, parameters=parameters,
                  run=runner, path=path)


def discover(directory) -> Tuple[List[Plugin], List[str]]:
    """Returns (plugins, problems). Never raises."""
    directory = Path(directory)
    plugins: List[Plugin] = []
    problems: List[str] = []
    if not directory.is_dir():
        return plugins, problems
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            plugins.append(load_plugin_file(path))
        except PluginError as exc:
            problems.append(f"{path.name}: {exc}")
    return plugins, problems


class PluginRegistry:
    def __init__(self, reserved=None):
        self.reserved = set(RESERVED) | set(reserved or ())
        self._plugins: Dict[str, Plugin] = {}
        self.problems: List[str] = []

    def register(self, plugin: Plugin) -> None:
        if plugin.name in self.reserved:
            raise PluginError(f"'{plugin.name}' is a reserved name")
        if plugin.name in self._plugins:
            raise PluginError(f"'{plugin.name}' is already registered")
        self._plugins[plugin.name] = plugin

    def load_directory(self, directory) -> List[str]:
        plugins, problems = discover(directory)
        self.problems = list(problems)
        for plugin in plugins:
            try:
                self.register(plugin)
            except PluginError as exc:
                self.problems.append(f"{plugin.path.name}: {exc}")
        return self.problems

    def get(self, name: str) -> Optional[Plugin]:
        return self._plugins.get(name)

    def names(self) -> List[str]:
        return sorted(self._plugins)

    def describe(self) -> List[Dict[str, Any]]:
        return [self._plugins[name].describe() for name in self.names()]

    def __len__(self) -> int:
        return len(self._plugins)

    def __contains__(self, name: object) -> bool:
        return name in self._plugins

    def run(self, name: str, args: Dict[str, Any], ctx: PluginContext) -> Result:
        plugin = self._plugins.get(name)
        if plugin is None:
            known = ", ".join(self.names()) or "none"
            return failed(f"Unknown plugin '{name}' (installed: {known})")
        try:
            result = plugin.run(dict(args or {}), ctx)
        except Exception as exc:
            return failed(f"Plugin '{name}' failed: {type(exc).__name__}: {exc}")
        if isinstance(result, Result):
            return result
        if isinstance(result, str) and result.strip():
            return ok(result.strip())
        if result is None:
            return unverified(f"Plugin '{name}' returned nothing")
        return ok(str(result))
