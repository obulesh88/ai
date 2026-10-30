"""HEMA facade: connects chat, memory, tasks, automation, coding, game dev, analytics, self-update."""
import json
from pathlib import Path
from typing import Iterator, List, Optional

from ai.ollama_client import OllamaError
from analytics.dragon_tiger import DragonTigerStore
from automation.app_manager import AppManager
from automation.command_runner import CommandRunner
from automation.file_manager import BackupManager, FileManager
from automation.process_monitor import list_processes
from coding.code_agent import CodeAgent
from coding.code_editor import CodeEditor
from coding.project_inspector import inspect_project, to_json
from config import Config
from core.assistant import Assistant
from core.command_router import route
from core.executor import TaskExecutor
from core.planner import Planner
from core.self_update import SelfUpdater
from core.task_manager import TaskManager
from game_development import mcp_integration
from memory.memory_manager import MemoryManager
from security.permissions import ApprovalManager, AuditLog, PermissionDenied, WorkspaceGuard


class Hema:
    def __init__(self, config: Config, approver=None):
        self.config = config
        self.data_dir = Path(config.data_dir)
        self.audit = AuditLog(config.logs_dir / "audit.log")
        self.approvals = ApprovalManager(self.audit, approver)
        self.guard = WorkspaceGuard(config.workspace_dir)
        self.backups = BackupManager(config.backups_dir)

        self.assistant = Assistant(config)
        self.memory = MemoryManager(self.data_dir / "hema_memory.db")
        self.tasks = TaskManager(self.data_dir / "hema_tasks.db")
        self.dt = DragonTigerStore(self.data_dir / "dragon_tiger.db")
        self.files = FileManager(self.guard, self.approvals, self.backups)
        self.editor = CodeEditor(self.files)
        self.commands = CommandRunner(self.approvals, self.guard)
        self.apps = AppManager(self.approvals)
        self.code_agent = CodeAgent(self._chat_once, self.editor, self.guard.root)
        self.planner = Planner(lambda msgs: self._chat_once(msgs))
        self.self_updater = SelfUpdater(Path(__file__).resolve().parent.parent,
                                       self.approvals, self.backups)
        self.recovered = self.tasks.recover()

    # ---- helpers -------------------------------------------------
    def _chat_once(self, messages: List[dict]) -> str:
        return self.assistant.client.chat(self._model(), messages)

    def _model(self) -> str:
        if self.assistant.models.current is None:
            self.assistant.models.auto_select()
        return self.assistant.models.current

    def status(self) -> dict:
        return {
            "ollama_host": self.config.ollama_host,
            "model": self.assistant.models.current,
            "workspace": str(self.guard.root),
            "unfinished_tasks": len(self.tasks.unfinished()),
            "memories": len(self.memory.list()),
        }

    # ---- main entry ----------------------------------------------
    def handle(self, text: str) -> Iterator[str]:
        """Generator: yields response text chunks so the UI can stream."""
        intent = route(text)
        handler = getattr(self, f"_do_{intent.kind}", None)
        try:
            if handler is None:
                output = self._do_chat(intent)
            else:
                output = handler(intent)
            if output is None:
                return
            if isinstance(output, str):
                yield output
            else:
                yield from output
        except PermissionDenied as e:
            self.audit.record("blocked", f"{intent.kind}: {e}", "denied")
            yield f"Not permitted: {e}"
        except OllamaError as e:
            self.audit.record("error", f"{intent.kind}: {e}", "error")
            yield f"Ollama error: {e}"
        except Exception as e:
            self.audit.record("error", f"{intent.kind}: {type(e).__name__}: {e}", "error")
            yield f"{type(e).__name__}: {e}"

    # ---- intents -------------------------------------------------
    def _do_chat(self, intent) -> Iterator[str]:
        pieces = []
        for chunk in self.assistant.ask(intent.args["text"]):
            pieces.append(chunk)
            yield chunk
        answer = "".join(pieces)
        self.memory.add_message("user", intent.args["text"])
        self.memory.add_message("assistant", answer)

    def _do_empty(self, intent):
        return ""

    def _do_help(self, intent):
        return (
            "I can: chat, 'plan: <request>', 'show tasks', 'remember: <fact>', "
            "'recall <text>', 'forget <id>', 'inspect: <path>', 'open <app>', "
            "'run: <command>', 'list processes', 'dragon|tiger|tie result', "
            "'dragon tiger stats', 'run with windows', 'update yourself'."
        )

    def _do_remember(self, intent):
        mid = self.memory.add("note", intent.args["content"])
        return f"Saved to memory #{mid}."

    def _do_recall(self, intent):
        rows = self.memory.search(intent.args["text"])
        if not rows:
            return "Nothing found in memory."
        return "\n".join(f"#{r['id']} [{r['kind']}] {r['content']}" for r in rows)

    def _do_forget(self, intent):
        mid = int(intent.args["id"])
        self.approvals.require("delete-memory", f"Memory #{mid}")
        return f"Deleted memory #{mid}." if self.memory.delete(mid) else f"Memory #{mid} not found."

    def _do_tasks(self, intent):
        rows = self.tasks.list()
        if not rows:
            return "No tasks yet."
        return "\n".join(
            f"#{t.id} [{t.status}{'/verified' if t.verified else ''}] {t.progress}% {t.description[:60]}"
            for t in rows)

    def _do_plan(self, intent):
        plan = self.planner.make_plan(intent.args["request"])
        ids = []
        for step in plan.steps:
            ids.append(self.tasks.create(step, [step], ["chat"], priority=3))
        lines = [f"Plan ({plan.source}) created with {len(ids)} task(s):"]
        lines += [f"#{i} {s}" for i, s in zip(ids, plan.steps)]
        return "\n".join(lines)

    def _do_inspect(self, intent):
        raw = intent.args["text"]
        path = self.guard.resolve(raw) if not Path(raw).is_absolute() else Path(raw)
        if not Path(path).is_dir():
            path = self.guard.root
        return to_json(inspect_project(path))

    def _do_open_app(self, intent):
        return f"Launched {self.apps.launch(intent.args['app'])}."

    def _do_run_command(self, intent):
        code, out = self.commands.run(intent.args["text"])
        return f"exit={code}\n{out}"

    def _do_processes(self, intent):
        return "\n".join(list_processes(intent.args.get("filter", "")))

    def _do_dt_record(self, intent):
        rid = self.dt.add(intent.args["outcome"])
        return f"Recorded {intent.args['outcome']} (row {rid}).\n" + self.dt.report_text()

    def _do_dt_stats(self, intent):
        return self.dt.report_text()

    def _do_startup_install(self, intent):
        from automation.startup import install_startup
        script = install_startup(self.config.base_dir if hasattr(self.config, "base_dir")
                                 else Path(__file__).resolve().parent.parent, self.approvals)
        return f"Windows startup launcher installed at {script}."

    def _do_self_update(self, intent):
        report = self.self_updater.inspect()
        return ("Self-inspection:\n" + json.dumps(
            {"syntax_errors": report["syntax_errors"], "tests_ok": report["tests_ok"]}, indent=2)
            + "\nTo change code, call SelfUpdater.apply() with proposed changes and approval.")

    def _do_mcp(self, intent):
        servers = mcp_integration.load_servers([self.config.mcp_config] if self.config.mcp_config else [])
        return to_json(mcp_integration.describe(servers))

    # ---- extras used by the UI -----------------------------------
    def run_task(self, task_id: int, action, tool: str = None) -> dict:
        return TaskExecutor(self.tasks, {}, max_retries=1).run(task_id, action, tool)

    def close(self) -> None:
        for obj in (self.memory, self.tasks, self.dt):
            try:
                obj.close()
            except Exception:
                pass
