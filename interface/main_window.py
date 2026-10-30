"""HEMA desktop dashboard: top navigation, sidebar, workspace and right rail."""
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QMainWindow, QPushButton, QSizePolicy, QStackedWidget,
                               QVBoxLayout, QWidget)

from interface import settings_store, system_stats, theme
from interface.pages import (ChatPage, GameDevPage, HistoryPage, MemoryPage, SettingsPage,
                             TasksPage, UnityPage, UnrealPage)
from interface.widgets import (GlassPanel, LogoMark, MeterRow, StatusDot, configure_list,
                               elide)

NAV_ITEMS = (
    ("chat", "+", "New Chat"),
    ("history", "\u2261", "Chat History"),
    ("game", "\u25B6", "Game Development"),
    ("unity", "\u25A3", "Unity Tools"),
    ("unreal", "\u25B2", "Unreal Engine Tools"),
    ("memory", "\u25C9", "Memory"),
    ("tasks", "\u2713", "Tasks"),
    ("settings", "\u2699", "Settings"),
)
PAGE_ORDER = tuple(key for key, _, _ in NAV_ITEMS)
NETWORK_SCALE_BPS = 10 * 1024 * 1024


class ChatWorker(QThread):
    """Runs one HEMA request off the UI thread and streams chunks back."""

    chunk = Signal(str)
    done = Signal()
    failed = Signal(str)

    def __init__(self, controller, text: str):
        super().__init__()
        self.controller = controller
        self.text = text

    def run(self):
        try:
            for piece in self.controller.ask(self.text):
                if self.isInterruptionRequested():
                    break
                self.chunk.emit(piece)
            self.done.emit()
        except Exception as e:  # never let a worker crash the UI
            self.failed.emit(f"{type(e).__name__}: {e}")


class ProbeWorker(QThread):
    """Checks Ollama/model availability without blocking the window."""

    result = Signal(object, str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        try:
            models = self.controller.models()
            if not models:
                self.result.emit([], "Ollama unreachable - cannot connect to " + self.controller.ollama_host())
                return
            self.result.emit(models, f"{len(models)} model(s) available")
        except Exception as e:
            self.result.emit([], str(e))


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.worker = None
        self.probe = None
        self._pending_id = None
        self._last_log_pos = 0
        self._busy = False

        self.setWindowTitle("HEMA AI")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 740)

        root = QWidget()
        root.setObjectName("RootBackground")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 12, 14, 8)
        outer.setSpacing(10)
        outer.addWidget(self._build_top_bar())
        outer.addWidget(self._build_approval_banner())

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._build_sidebar(), 0)
        body.addWidget(self._build_workspace(), 1)
        body.addWidget(self._build_right_rail(), 0)
        outer.addLayout(body, 1)
        self.setCentralWidget(root)

        self.statusBar().showMessage("Starting HEMA...")
        self._timers = []
        self._start_timer(2000, self._update_stats)
        self._start_timer(1500, self._poll_activity)
        self._start_timer(500, self._poll_approvals)

        self._apply_saved_settings()
        self.apply_identity()
        self._update_empty_state()
        self._update_stats()
        self.goto("chat")
        QTimer.singleShot(180, self._probe_connection)

    def apply_identity(self) -> None:
        """Applies the configured names to the title, greeting and prompt (already set)."""
        identity = self.controller.identity()
        self.setWindowTitle(identity.window_title())
        self.title_label.setText(identity.assistant_name.upper())
        self.page_chat.set_greeting(identity)
        self.statusBar().showMessage(
            f"{identity.assistant_name} ready for {identity.user_name}")

    def _apply_saved_settings(self) -> None:
        """Restores the saved timeout and model preference (the URL stays in .env)."""
        self._saved_model = ""
        try:
            saved = settings_store.load(self.controller.hema.config.data_dir)
            if saved.get("timeout"):
                self.controller.hema.assistant.client.timeout = float(saved["timeout"])
            self._saved_model = saved.get("model") or ""
        except Exception as e:
            self.statusBar().showMessage(f"Could not load settings: {e}")

    def _start_timer(self, ms: int, slot):
        timer = QTimer(self)
        timer.timeout.connect(slot)
        timer.start(ms)
        self._timers.append(timer)

    # ------------------------------------------------------------------ top bar
    def _build_top_bar(self) -> QWidget:
        panel = GlassPanel(compact=True)
        panel.title_label.hide()
        panel.setFixedHeight(66)
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(LogoMark(34))
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("HEMA AI")
        title.setObjectName("AppTitle")
        self.title_label = title
        subtitle = QLabel("LOCAL NEURAL ASSISTANT")
        self.subtitle_label = subtitle
        subtitle.setObjectName("AppSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        row.addLayout(title_col)
        row.addStretch(1)

        self.status_dot = StatusDot()
        self.conn_pill = QLabel("CHECKING...")
        self.conn_pill.setObjectName("StatusPill")
        row.addWidget(self.status_dot)
        row.addWidget(self.conn_pill)

        self.model_chip = QLabel("MODEL -")
        self.model_chip.setObjectName("StatusPill")
        self.model_chip.setMinimumWidth(150)
        self.model_chip.setAlignment(Qt.AlignCenter)
        row.addWidget(self.model_chip)

        self.host_chip = QLabel(self.controller.ollama_host())
        self.host_chip.setObjectName("StatusPill")
        row.addWidget(self.host_chip)

        settings_button = QPushButton("\u2699  Settings")
        settings_button.setObjectName("Small")
        settings_button.setCursor(Qt.PointingHandCursor)
        settings_button.clicked.connect(lambda: self.goto("settings"))
        row.addWidget(settings_button)

        panel.add_layout(row)
        return panel

    def _build_approval_banner(self) -> QWidget:
        self.banner = QWidget()
        row = QHBoxLayout(self.banner)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.banner_label = QLabel("")
        self.banner_label.setObjectName("ApprovalBanner")
        self.banner_label.setWordWrap(True)
        allow = QPushButton("Allow")
        allow.setObjectName("Primary")
        allow.setCursor(Qt.PointingHandCursor)
        allow.setMinimumWidth(84)
        deny = QPushButton("Deny")
        deny.setObjectName("Small")
        deny.setCursor(Qt.PointingHandCursor)
        allow.clicked.connect(lambda: self._decide_approval(True))
        deny.clicked.connect(lambda: self._decide_approval(False))
        row.addWidget(self.banner_label, 1)
        row.addWidget(allow)
        row.addWidget(deny)
        self.banner.setVisible(False)
        return self.banner

    # ------------------------------------------------------------------ sidebar
    def _build_sidebar(self) -> QWidget:
        col = QWidget()
        col.setFixedWidth(232)
        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        nav = GlassPanel("Navigation", compact=True)
        self.nav_buttons = {}
        for index, (key, glyph, label) in enumerate(NAV_ITEMS):
            if index in (2, 5):
                spacer = QWidget()
                spacer.setFixedHeight(1)
                nav.add(spacer)
            button = QPushButton(f"{glyph}   {label}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(38)
            button.clicked.connect(lambda _=False, k=key: self.goto(k))
            nav.add(button)
            self.nav_buttons[key] = button
        layout.addWidget(nav)

        info = GlassPanel("Session", compact=True)
        self.rail_workspace = QLabel()
        self.rail_workspace.setObjectName("RailValue")
        self.rail_workspace.setWordWrap(True)
        info.add(self.rail_workspace)
        self.rail_unfinished = QLabel()
        self.rail_unfinished.setObjectName("PageHint")
        info.add(self.rail_unfinished)
        layout.addWidget(info)
        layout.addStretch(1)
        version = QLabel("HEMA 1.0  \u2022  Segment 2")
        version.setObjectName("PageHint")
        layout.addWidget(version)
        return col

    # ---------------------------------------------------------------- workspace
    def _build_workspace(self) -> QWidget:
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.page_chat = ChatPage(self.controller)
        self.page_chat.send_requested.connect(self.send_message)
        self.page_chat.stop_requested.connect(self.stop_generation)
        self.page_chat.clear_requested.connect(self.clear_chat)
        self.avatar = self.page_chat.avatar
        self.chat = self.page_chat.chat
        self.input = self.page_chat.input
        self.send_btn = self.page_chat.send_btn
        self.stop_btn = self.page_chat.stop_btn
        self.greeting = self.page_chat.greeting

        self.page_history = HistoryPage(self.controller)
        self.page_game = GameDevPage(self.controller)
        self.page_unity = UnityPage(self.controller)
        self.page_unreal = UnrealPage(self.controller)
        self.page_memory = MemoryPage(self.controller)
        self.page_tasks = TasksPage(self.controller)
        self.page_settings = SettingsPage(self.controller)
        self.pages = {
            "chat": self.page_chat,
            "history": self.page_history,
            "game": self.page_game,
            "unity": self.page_unity,
            "unreal": self.page_unreal,
            "memory": self.page_memory,
            "tasks": self.page_tasks,
            "settings": self.page_settings,
        }
        for key in PAGE_ORDER:
            self.stack.addWidget(self.pages[key])
        return self.stack

    # --------------------------------------------------------------- right rail
    def _build_right_rail(self) -> QWidget:
        col = QWidget()
        col.setFixedWidth(312)
        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        system = GlassPanel("System", compact=True)
        self.meter_cpu = MeterRow("CPU")
        self.meter_mem = MeterRow("Memory")
        self.meter_disk = MeterRow("Disk")
        system.add(self.meter_cpu)
        system.add(self.meter_mem)
        system.add(self.meter_disk)
        self.rail_net = QLabel("--")
        self.rail_net.setObjectName("RailValue")
        system.add(self.rail_net)
        layout.addWidget(system)

        model = GlassPanel("Model", compact=True)
        self.rail_model = QLabel("not selected")
        self.rail_model.setObjectName("RailValue")
        self.rail_model.setWordWrap(True)
        self.rail_status = QLabel("checking connection...")
        self.rail_status.setObjectName("PageHint")
        self.rail_status.setWordWrap(True)
        model.add(self.rail_model)
        model.add(self.rail_status)
        layout.addWidget(model)

        activity = GlassPanel("Activity", compact=True)
        self.activity_list = QListWidget()
        configure_list(self.activity_list)
        activity.add(self.activity_list, 1)
        layout.addWidget(activity, 3)

        tasks = GlassPanel("Running tasks", compact=True)
        self.rail_tasks = QLabel("0 pending")
        self.rail_tasks.setObjectName("RailValue")
        tasks.add(self.rail_tasks)
        self.rail_task_list = QListWidget()
        configure_list(self.rail_task_list)
        tasks.add(self.rail_task_list, 1)
        layout.addWidget(tasks, 2)

        memory = GlassPanel("Memory", compact=True)
        self.rail_memory = QLabel("0 memories")
        self.rail_memory.setObjectName("RailValue")
        self.memory_snippet = QLabel("")
        self.memory_snippet.setObjectName("PageHint")
        self.memory_snippet.setWordWrap(True)
        memory.add(self.rail_memory)
        memory.add(self.memory_snippet)
        layout.addWidget(memory)
        return col

    # --------------------------------------------------------------- navigation
    def goto(self, key: str) -> None:
        if key not in self.pages:
            return
        self.stack.setCurrentWidget(self.pages[key])
        for name, button in self.nav_buttons.items():
            button.setChecked(name == key)
        page = self.pages[key]
        self._last_key = key
        try:
            page.refresh()
        except Exception as e:
            self.statusBar().showMessage(f"Could not refresh {key}: {e}")
        if key == "chat":
            self.input.setFocus()
        self.statusBar().showMessage(f"{key.title()} view")

    def current_page_key(self) -> str:
        current = self.stack.currentWidget()
        for key, page in self.pages.items():
            if page is current:
                return key
        return "chat"

    # -------------------------------------------------------------------- chat
    def send_message(self, text: str = None) -> None:
        text = (text if text is not None else self.input.text()).strip()
        if not text:
            return
        if self._busy or (self.worker and self.worker.isRunning()):
            # keep what the user typed instead of silently dropping it
            self.input.setText(text)
            self.statusBar().showMessage("Still answering - your message is waiting in the box")
            return
        if self.current_page_key() != "chat":
            self.goto("chat")
        self.input.clear()
        self.chat.add("user", text)
        self.chat.begin_stream()
        self.page_chat.show_empty_state(False)
        self.avatar.set_state("thinking")
        self.status_dot.set_state("busy")
        self._busy = True
        self.page_chat.set_busy(True)
        self.statusBar().showMessage("HEMA is thinking...")
        self.worker = ChatWorker(self.controller, text)
        self.worker.chunk.connect(self._on_chunk)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_chunk(self, text: str) -> None:
        self.chat.append_stream(text)

    def _on_done(self) -> None:
        final = self.chat.end_stream()
        self._busy = False
        self.page_chat.set_busy(False)
        lowered = final.lower()
        failed = any(token in lowered for token in
                     ("ollama error", "not permitted", "not approved", "permissiondenied"))
        if failed:
            self.avatar.set_state("error")
            self.status_dot.set_state("offline" if "ollama error" in lowered else "online")
            self.statusBar().showMessage("Request failed - see the message above")
        else:
            self.avatar.set_state("idle")
            self.status_dot.set_state("online")
            self.statusBar().showMessage("Ready")
        self._refresh_rail()

    def _on_failed(self, message: str) -> None:
        self.chat.end_stream()
        self.chat.add("error", message)
        self.avatar.set_state("error")
        self.status_dot.set_state("offline")
        self._busy = False
        self.page_chat.set_busy(False)
        self.statusBar().showMessage("Error: " + message)

    def stop_generation(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(3000)
            self.chat.end_stream(" [stopped]")
            self.avatar.set_state("idle")
            self.status_dot.set_state("online")
            self._busy = False
            self.page_chat.set_busy(False)
            self.statusBar().showMessage("Stopped by you")

    def clear_chat(self) -> None:
        self.chat.clear_all()
        self.controller.hema.assistant.conversation.clear()
        self.controller.hema.audit.record("clear-chat", "visible transcript + context",
                                          "approved (GUI button)")
        self._update_empty_state()
        self.statusBar().showMessage("Chat cleared (stored history kept)")

    def _update_empty_state(self) -> None:
        empty = self.chat.is_empty()
        self.page_chat.show_empty_state(empty)

    # -------------------------------------------------------------- connection
    def _probe_connection(self) -> None:
        self.conn_pill.setText("CHECKING...")
        self.status_dot.set_state("idle")
        self.probe = ProbeWorker(self.controller)
        self.probe.result.connect(self._on_probe)
        self.probe.start()

    def _on_probe(self, models, message: str) -> None:
        if models:
            current = self.controller.hema.assistant.models.current
            if not current and models:
                preference = self._saved_model or self.controller.ui_model()
                pick = preference if preference in models else (
                    preference + ":latest" if preference + ":latest" in models else models[0])
                try:
                    current = self.controller.select_model(pick)
                except Exception:
                    current = models[0]
            self.conn_pill.setText("ONLINE")
            self.conn_pill.setStyleSheet(
                f"color:{theme.OK}; border:1px solid {theme.OK}; border-radius:10px;"
                "padding:4px 10px; font-size:11px;")
            self.status_dot.set_state("online")
            self.model_chip.setText(f"MODEL  {current or '-'}")
            elide(self.model_chip, f"MODEL  {current or '-'}", 190)
            self.rail_model.setText(current or "not selected")
            self.rail_status.setText(f"Ollama reachable ({message})")
            self.avatar.set_state("idle")
            self.statusBar().showMessage(f"Connected - {message}")
        else:
            self.conn_pill.setText("OFFLINE")
            self.conn_pill.setStyleSheet(
                f"color:{theme.DANGER}; border:1px solid {theme.DANGER}; border-radius:10px;"
                "padding:4px 10px; font-size:11px;")
            self.status_dot.set_state("offline")
            self.model_chip.setText("MODEL  -")
            self.rail_model.setText("not connected")
            self.rail_status.setText(message)
            self.avatar.set_state("error")
            self.statusBar().showMessage(message)
            self.chat.add("error", message +
                          "\nStart Ollama, then use Settings > Reconnect.")
            self.page_chat.show_empty_state(False)
        self._refresh_rail()

    # ------------------------------------------------------------------- timers
    def _update_stats(self) -> None:
        snapshot = system_stats.snapshot()
        cpu = snapshot["cpu"]
        self.meter_cpu.set_value(cpu, f"{cpu:.0f}%" if cpu is not None else "n/a")
        mem_pct = snapshot["mem_percent"]
        self.meter_mem.set_value(
            mem_pct,
            f"{system_stats.human_bytes(snapshot['mem_used'])} / "
            f"{system_stats.human_bytes(snapshot['mem_total'])}")
        self.meter_disk.set_value(
            snapshot["disk_percent"],
            "free " + system_stats.human_bytes(snapshot["disk_free"]))
        down = snapshot["down_bps"]
        up = snapshot["up_bps"]
        if down is None:
            self.rail_net.setText("network  n/a")
        else:
            self.rail_net.setText(f"\u2193 {system_stats.human_bytes(down, '/s')}   "
                                  f"\u2191 {system_stats.human_bytes(up, '/s')}")

    def _poll_activity(self) -> None:
        self._render_activity()
        self._tail_log()

    def _render_activity(self) -> None:
        entries = self.controller.audit_tail(40)
        self.activity_list.clear()
        chat_lines = list(self.controller.log[-6:])
        if not entries and not chat_lines:
            self.activity_list.addItem("(no activity yet)")
        for entry in reversed(entries[-10:]):
            outcome = entry["outcome"]
            item = QListWidgetItem(f"{entry['time'][11:]}  {entry['action']}  [{outcome}]")
            from PySide6.QtGui import QColor
            if "denied" in outcome:
                item.setForeground(QColor(theme.DANGER))
            elif outcome.startswith("approved"):
                item.setForeground(QColor(theme.OK))
            item.setToolTip(entry["detail"])
            self.activity_list.addItem(item)
        for line in reversed(chat_lines):
            item = QListWidgetItem(f"chat     {line[:60]}")
            from PySide6.QtGui import QColor
            item.setForeground(QColor(theme.TEXT_DIM))
            self.activity_list.addItem(item)

    def _tail_log(self) -> None:
        log_path = Path(self.controller.hema.config.logs_dir) / "hema.log"
        if not log_path.is_file():
            return
        try:
            size = log_path.stat().st_size
            if size < self._last_log_pos:
                self._last_log_pos = 0
            with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
                handle.seek(self._last_log_pos)
                self._last_log_pos = handle.tell()
        except OSError:
            return

    def _poll_approvals(self) -> None:
        pending = self.controller.pending_approvals()
        if not pending:
            if self.banner.isVisible():
                self.banner.setVisible(False)
                self._pending_id = None
            return
        first = pending[0]
        self._pending_id = first["id"]
        self.banner_label.setText(f"Permission needed - {first['action']}: {first['detail']}")
        self.banner.setVisible(True)

    def _decide_approval(self, allow: bool) -> None:
        if self._pending_id is None:
            return
        self.controller.decide_approval(self._pending_id, allow)
        self.statusBar().showMessage("Permission " + ("granted" if allow else "denied"))
        self._pending_id = None
        self.banner.setVisible(False)

    # -------------------------------------------------------------------- rail
    def _refresh_rail(self) -> None:
        try:
            self.rail_workspace.setText(self.controller.workspace_path())
            unfinished = len(self.controller.hema.tasks.unfinished())
            plural = "" if unfinished == 1 else "s"
            self.rail_unfinished.setText(f"{unfinished} unfinished task{plural}")
            self.rail_tasks.setText(f"{unfinished} pending")
            self.rail_task_list.clear()
            tasks = self.controller.tasks()
            if not tasks:
                self.rail_task_list.addItem("(none)")
            for task in tasks[-5:]:
                self.rail_task_list.addItem(f"#{task.id} {task.status} {task.progress}%")
            memories = self.controller.memories()
            label = "memory" if len(memories) == 1 else "memories"
            self.rail_memory.setText(f"{len(memories)} {label}")
            last = memories[-1]["content"] if memories else ""
            self.memory_snippet.setText(elide_text(last, 60) or "nothing stored yet")
            current = self.controller.hema.assistant.models.current
            if current:
                self.rail_model.setText(current)
        except Exception as e:
            self.statusBar().showMessage(f"Rail refresh failed: {e}")

    # -------------------------------------------------------------------- close
    def closeEvent(self, event):
        for timer in self._timers:
            timer.stop()
        try:
            self.page_settings.shutdown()
        except Exception:
            pass
        for thread in (self.worker, self.probe):
            if thread is not None and thread.isRunning():
                thread.requestInterruption()
                if not thread.wait(3000):
                    thread.terminate()
                    thread.wait(500)
        try:
            self.controller.hema.close()
        except Exception:
            pass
        super().closeEvent(event)


def elide_text(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."
