"""Workspace pages behind the sidebar navigation. Every page shows real data."""
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox, QPushButton,
                               QSpinBox, QVBoxLayout, QWidget)

from interface import settings_store, theme
from interface.widgets import (ChatView, GlassPanel, HoloAvatar, chip, configure_list,
                               elide)


def page_header(title: str, hint: str = "") -> tuple:
    box = QWidget()
    layout = QHBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    title_label = QLabel(title)
    title_label.setObjectName("PageTitle")
    text_col.addWidget(title_label)
    hint_label = QLabel(hint)
    hint_label.setObjectName("PageHint")
    hint_label.setWordWrap(True)
    text_col.addWidget(hint_label)
    layout.addLayout(text_col, 1)
    return box, layout


def small_button(text: str, slot, primary: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("Primary" if primary else "Small")
    button.clicked.connect(slot)
    button.setCursor(Qt.PointingHandCursor)
    return button


class BasePage(QWidget):
    """Page with a title, hint and optional action buttons."""

    title = "Page"
    hint = ""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(4, 2, 4, 2)
        self.root.setSpacing(10)
        header, layout = page_header(self.title, self.hint)
        self.header_box = header
        self.header_layout = layout
        self.root.addWidget(header)

    def add_action(self, button: QPushButton) -> QPushButton:
        self.header_layout.addWidget(button)
        return button

    def refresh(self) -> None:  # pragma: no cover - overridden
        pass


class ChatPage(QWidget):
    """Holographic avatar, greeting/empty state, messages and composer."""

    send_requested = Signal(str)
    stop_requested = Signal()
    clear_requested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self.holo_panel = GlassPanel("Holographic interface")
        self.holo_panel.setMinimumHeight(196)
        self.avatar = HoloAvatar()
        self.avatar.setMinimumSize(180, 180)
        self.holo_panel.add(self.avatar, 1)
        self.greeting = QLabel("")
        self.greeting.setObjectName("Greeting")
        self.greeting.setAlignment(Qt.AlignCenter)
        self.greeting.setWordWrap(True)
        self.greeting_hint = QLabel("")
        self.greeting_hint.setObjectName("PageHint")
        self.greeting_hint.setAlignment(Qt.AlignCenter)
        self.greeting_hint.setWordWrap(True)
        self.holo_panel.add(self.greeting)
        self.holo_panel.add(self.greeting_hint)
        root.addWidget(self.holo_panel, 4)

        self.chat_panel = GlassPanel("Conversation")
        self.clear_button = small_button("Clear chat", self.clear_requested.emit)
        self.chat_panel.add_action(self.clear_button)
        self.chat = ChatView()
        self.chat.setMinimumHeight(160)
        self.chat_panel.add(self.chat, 1)

        composer = QHBoxLayout()
        composer.setSpacing(8)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Message HEMA...   (Enter to send, /help for commands)")
        self.input.setMinimumHeight(42)
        self.input.returnPressed.connect(self._emit_send)
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("Primary")
        self.send_btn.setMinimumHeight(42)
        self.send_btn.setMinimumWidth(92)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self._emit_send)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("Ghost")
        self.stop_btn.setMinimumHeight(42)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        composer.addWidget(self.input, 1)
        composer.addWidget(self.send_btn)
        composer.addWidget(self.stop_btn)
        self.chat_panel.add_layout(composer)
        root.addWidget(self.chat_panel, 6)

    # --- state helpers
    def _emit_send(self):
        text = self.input.text().strip()
        if text:
            self.input.clear()
            self.send_requested.emit(text)

    def set_greeting(self, identity=None) -> None:
        from core.identity import Identity
        identity = identity or Identity()
        self.greeting.setText(identity.greeting())
        self.name = identity.assistant_name
        self.greeting_hint.setText(
            f"Ask {identity.assistant_name} anything, or try:  plan: build a snake game  |  "
            "remember: I use Unity 2022  |  dragon tiger stats")

    def show_empty_state(self, empty: bool) -> None:
        self.greeting.setVisible(empty)
        self.greeting_hint.setVisible(empty)
        self.avatar.setVisible(True)

    def set_busy(self, busy: bool) -> None:
        self.send_btn.setEnabled(not busy)
        self.stop_btn.setEnabled(busy)
        if not busy:
            self.input.setFocus()


class HistoryPage(BasePage):
    title = "Chat history"
    hint = "Conversation turns stored in the local SQLite memory (data/hema_memory.db)."

    def __init__(self, controller, parent=None):
        super().__init__(controller, parent)
        self.add_action(small_button("Refresh", self.refresh))
        self.add_action(small_button("Clear history", self.clear_history))
        panel = GlassPanel("Recent messages")
        self.list = QListWidget()
        configure_list(self.list)
        panel.add(self.list, 1)
        self.root.addWidget(panel, 1)
        self.status = QLabel("")
        self.status.setObjectName("PageHint")
        self.root.addWidget(self.status)

    def refresh(self):
        self.list.clear()
        rows = self.controller.hema.memory.recent_messages(200)
        if not rows:
            self.list.addItem("No conversation history yet - say something in Chat.")
        for row in rows:
            who = "You" if row["role"] == "user" else "HEMA"
            text = " ".join(row["content"].split())
            item = QListWidgetItem(f"{who:5s}  {text[:150]}")
            item.setForeground(Qt.cyan if row["role"] != "user" else Qt.gray)
            item.setToolTip(row["content"][:800])
            self.list.addItem(item)
        self.list.scrollToBottom()
        self.status.setText(f"{len(rows)} message(s) stored")

    def clear_history(self):
        if QMessageBox.question(self, "Clear history",
                                "Delete all stored conversation messages?") != QMessageBox.Yes:
            return
        self.controller.hema.audit.record("clear-history", "all messages",
                                          "approved (GUI confirmation)")
        self.controller.hema.memory.clear_messages()
        self.refresh()


def _find_projects(workspace: Path):
    from coding.project_inspector import detect_type
    found = {"unity": [], "unreal": [], "python": [], "generic": []}
    if not workspace.is_dir():
        return found
    for child in sorted(workspace.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        try:
            kind = detect_type(child)
        except OSError:
            continue
        found.setdefault(kind, []).append(child)
    return found


class GameDevPage(BasePage):
    title = "Game development"
    hint = ("Projects are discovered inside the approved workspace. Engine automation needs the "
            "editor plus a connected MCP server.")

    def __init__(self, controller, parent=None):
        super().__init__(controller, parent)
        self.add_action(small_button("Show tools", self.show_tools))
        self.add_action(small_button("Refresh", self.refresh))

        found = GlassPanel("Detected projects")
        self.projects = QListWidget()
        configure_list(self.projects)
        found.add(self.projects, 1)
        self.root.addWidget(found, 2)

        mcp = GlassPanel("MCP servers")
        self.mcp_list = QListWidget()
        configure_list(self.mcp_list)
        mcp.add(self.mcp_list, 1)
        self.root.addWidget(mcp, 2)

    def refresh(self):
        workspace = Path(self.controller.workspace_path())
        found = _find_projects(workspace)
        self.projects.clear()
        total = sum(len(v) for v in found.values())
        if not total:
            self.projects.addItem(f"No projects yet in {workspace}")
            self.projects.addItem("Create one with: run: unity -createProject ... (needs approval)")
        for kind in ("unity", "unreal", "python", "generic"):
            for path in found.get(kind, []):
                self.projects.addItem(f"{kind.upper():7s}  {path.name}")
        self.mcp_list.clear()
        servers = self.controller.mcp_servers()
        if not servers:
            self.mcp_list.addItem("No MCP servers configured (set HEMA_MCP_CONFIG in .env).")
        for server in servers:
            state = "ready" if server["command_found"] else "command not found"
            self.mcp_list.addItem(f"{server['name']}  ->  {state}")

    def show_tools(self):
        from interface.dialogs import ToolsDialog
        ToolsDialog(self.controller, self).exec()


class EnginePage(BasePage):
    """Shared page for Unity and Unreal tooling."""

    engine = "unity"

    def __init__(self, controller, parent=None):
        super().__init__(controller, parent)
        self.add_action(small_button("Refresh", self.refresh))
        info = GlassPanel(f"{self.engine.title()} projects")
        self.list = QListWidget()
        configure_list(self.list)
        info.add(self.list, 1)
        self.root.addWidget(info, 1)
        self.note = QLabel("")
        self.note.setObjectName("PageHint")
        self.note.setWordWrap(True)
        self.root.addWidget(self.note)

    def refresh(self):
        self.list.clear()
        workspace = Path(self.controller.workspace_path())
        from coding.project_inspector import detect_type
        projects = []
        if workspace.is_dir():
            for child in sorted(workspace.iterdir()):
                if child.is_dir() and detect_type(child) == self.engine:
                    projects.append(child)
        if not projects:
            self.list.addItem(f"No {self.engine} project found in {workspace}")
        for project in projects:
            try:
                if self.engine == "unity":
                    from game_development.unity import UnityProject
                    unity = UnityProject(project)
                    self.list.addItem(f"{project.name}  -  Unity {unity.editor_version()}")
                    self.list.addItem(f"    scenes: {len(unity.scenes())}   scripts: {len(unity.scripts())}")
                else:
                    from game_development.unreal import UnrealProject
                    unreal = UnrealProject(UnrealProject.find(project))
                    self.list.addItem(f"{project.name}  -  modules: {', '.join(unreal.modules()) or 'none'}")
            except Exception as e:
                self.list.addItem(f"{project.name}  -  could not inspect: {e}")
        self.note.setText(self.engine_hint(len(projects)))

    def engine_hint(self, count: int) -> str:
        return ""


class UnityPage(EnginePage):
    title = "Unity tools"
    hint = "Read-only inspection works now; creating GameObjects or scenes needs the Unity Editor."
    engine = "unity"

    def engine_hint(self, count: int) -> str:
        return (f"{count} Unity project(s) inspected from disk. Editor-level actions "
                "(create GameObject, add component, read Console) require a connected Unity MCP "
                "server and are not available yet.")


class UnrealPage(EnginePage):
    title = "Unreal Engine tools"
    hint = "C++ classes can be generated on disk; builds and editor actions need your approval."
    engine = "unreal"

    def engine_hint(self, count: int) -> str:
        return (f"{count} Unreal project(s) inspected from disk. Generating C++ classes and "
                "running approved build commands through the command runner is supported; "
                "Blueprint editing is not simulated.")


class MemoryPage(BasePage):
    title = "Memory"
    hint = "Long-term memories in SQLite. Secrets such as passwords and API keys are refused."

    def __init__(self, controller, parent=None):
        super().__init__(controller, parent)
        self.add_action(small_button("Refresh", self.refresh))
        self.add_action(small_button("Delete selected", self.delete_selected))
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search memories...")
        self.search.textChanged.connect(self.refresh)
        search_row.addWidget(self.search, 1)
        self.root.addLayout(search_row)
        panel = GlassPanel("Stored memories")
        self.list = QListWidget()
        configure_list(self.list)
        panel.add(self.list, 1)
        self.root.addWidget(panel, 1)
        self.count_label = QLabel("")
        self.count_label.setObjectName("PageHint")
        self.root.addWidget(self.count_label)

    def refresh(self):
        query = self.search.text().strip()
        rows = self.controller.hema.memory.search(query) if query else self.controller.memories()
        self.list.clear()
        if not rows:
            self.list.addItem("Nothing stored yet - try: remember: I build games in Unity 2022")
        for row in rows:
            item = QListWidgetItem(f"#{row['id']}  [{row['kind']}]  {row['content']}")
            item.setData(Qt.UserRole, row["id"])
            self.list.addItem(item)
        total = len(self.controller.memories())
        self.count_label.setText(f"{len(rows)} shown  |  {total} stored")

    def delete_selected(self):
        item = self.list.currentItem()
        memory_id = item.data(Qt.UserRole) if item else None
        if not memory_id:
            return
        if QMessageBox.question(self, "Delete memory",
                                f"Delete memory #{memory_id}?") != QMessageBox.Yes:
            return
        self.controller.delete_memory_confirmed(int(memory_id))
        self.refresh()


class TasksPage(BasePage):
    title = "Tasks"
    hint = "Tasks created by the planner, with live status, progress and completion reports."

    def __init__(self, controller, parent=None):
        super().__init__(controller, parent)
        self.add_action(small_button("Refresh", self.refresh))
        self.add_action(small_button("Cancel selected", self.cancel_selected))
        panel = GlassPanel("Task queue")
        self.list = QListWidget()
        configure_list(self.list)
        self.list.currentItemChanged.connect(self.show_detail)
        panel.add(self.list, 1)
        self.root.addWidget(panel, 1)
        self.detail = QLabel("Select a task to see its report.")
        self.detail.setObjectName("PageHint")
        self.detail.setWordWrap(True)
        self.root.addWidget(self.detail)

    def refresh(self):
        self.list.clear()
        rows = self.controller.tasks()
        if not rows:
            self.list.addItem("No tasks yet - try: plan: build a pong game")
        for task in rows:
            state = "verified" if task.verified else task.status
            item = QListWidgetItem(f"#{task.id}  [{state}]  {task.progress}%  {task.description[:70]}")
            item.setData(Qt.UserRole, (task.id, task.status, task.report or "(no report yet)"))
            self.list.addItem(item)

    def show_detail(self, current, previous=None):
        if current is None:
            return
        _, status, report = current.data(Qt.UserRole)
        self.detail.setText(f"status: {status}\n{report}")

    def cancel_selected(self):
        item = self.list.currentItem()
        payload = item.data(Qt.UserRole) if item else None
        if not payload:
            return
        task_id = payload[0]
        self.controller.hema.tasks.cancel(int(task_id))
        self.controller.hema.audit.record("cancel-task", f"Task #{task_id}",
                                          "approved (GUI confirmation)")
        self.refresh()


class _ModelsWorker(QThread):
    """Lists installed models off the UI thread so the window never blocks."""

    loaded = Signal(object, str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        try:
            self.loaded.emit(self.controller.models(), "")
        except Exception as e:
            self.loaded.emit([], str(e))


class SettingsPage(BasePage):
    title = "Settings"
    hint = "The Ollama URL comes from .env. Model choices are saved to data/settings.json."

    def __init__(self, controller, parent=None):
        super().__init__(controller, parent)
        self.add_action(small_button("Reconnect", self.reconnect))

        conn = GlassPanel("Connection")
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        rows = (("OLLAMA URL", controller.ollama_host()),
                ("WORKSPACE", controller.workspace_path()),
                ("CONFIG", ".env  (OLLAMA_HOST, HEMA_MODEL)"),
                ("UI SETTINGS", str(Path(controller.hema.config.data_dir) / "settings.json")))
        for index, (key, value) in enumerate(rows):
            label = QLabel(key)
            label.setObjectName("RailLabel")
            value_label = QLabel(value)
            value_label.setObjectName("RailValue")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label.setWordWrap(True)
            grid.addWidget(label, index, 0, Qt.AlignTop)
            grid.addWidget(value_label, index, 1)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 2)
        for row_index in range(len(rows)):
            grid.setColumnMinimumWidth(0, 110)
        conn.add_layout(grid)
        self.root.addWidget(conn)

        models = GlassPanel("Model")
        row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(220)
        self.apply_btn = small_button("Use now", self.apply_model, primary=True)
        model_label = QLabel("MODEL")
        model_label.setObjectName("RailLabel")
        row.addWidget(model_label)
        row.addWidget(self.model_combo, 1)
        row.addWidget(self.apply_btn)
        models.add_layout(row)
        row2 = QHBoxLayout()
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 600)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.setValue(int(controller.hema.config.timeout))
        self.save_btn = small_button("Save settings", self.save_settings, primary=True)
        timeout_label = QLabel("REQUEST TIMEOUT")
        timeout_label.setObjectName("RailLabel")
        row2.addWidget(timeout_label)
        row2.addWidget(self.timeout_spin)
        row2.addStretch(1)
        row2.addWidget(self.save_btn)
        models.add_layout(row2)
        self.status = QLabel("")
        self.status.setObjectName("PageHint")
        self.status.setWordWrap(True)
        models.add(self.status)
        self._worker = None
        self._model_cache = []
        self.root.addWidget(models)

        identity = GlassPanel("Identity")
        identity_row = QHBoxLayout()
        self.user_name_edit = QLineEdit()
        self.user_name_edit.setMaxLength(24)
        self.assistant_name_edit = QLineEdit()
        self.assistant_name_edit.setMaxLength(24)
        user_label = QLabel("YOUR NAME")
        user_label.setObjectName("RailLabel")
        assistant_label = QLabel("ASSISTANT NAME")
        assistant_label.setObjectName("RailLabel")
        self.save_identity_btn = small_button("Save names", self.save_identity, primary=True)
        identity_row.addWidget(user_label)
        identity_row.addWidget(self.user_name_edit, 1)
        identity_row.addWidget(assistant_label)
        identity_row.addWidget(self.assistant_name_edit, 1)
        identity_row.addWidget(self.save_identity_btn)
        identity.add_layout(identity_row)
        self.identity_status = QLabel("Used in the greeting, window title "
                                      "and the model's instructions.")
        self.identity_status.setObjectName("PageHint")
        self.identity_status.setWordWrap(True)
        identity.add(self.identity_status)
        self.root.addWidget(identity)
        self.root.addStretch(1)

    def refresh(self):
        saved = settings_store.load(self.controller.hema.config.data_dir)
        if saved.get("timeout"):
            self.timeout_spin.setValue(int(float(saved["timeout"])))
        identity = self.controller.identity()
        self.user_name_edit.setText(identity.user_name)
        self.assistant_name_edit.setText(identity.assistant_name)
        self.status.setText("Loading installed models...")
        if self._worker is not None and self._worker.isRunning():
            return
        self._worker = _ModelsWorker(self.controller)
        self._worker.loaded.connect(self._on_models)
        self._worker.start()

    def shutdown(self):
        """Stops the model-listing worker so no signal can land on a dead widget."""
        worker = self._worker
        self._worker = None
        if worker is None:
            return
        try:
            worker.loaded.disconnect()
        except (RuntimeError, TypeError):
            pass
        if worker.isRunning():
            worker.requestInterruption()
            if not worker.wait(2500):
                worker.terminate()
                worker.wait(500)

    def _on_models(self, models, error):
        self.model_combo.clear()
        self._model_cache = list(models or [])
        if not self._model_cache:
            self.model_combo.addItem("Ollama unreachable - start 'ollama serve'")
            self.model_combo.setEnabled(False)
            self.apply_btn.setEnabled(False)
            self.status.setText("Cannot list models: " + (error or "no models installed") +
                                " (" + self.controller.ollama_host() + ")")
            return
        self.model_combo.setEnabled(True)
        self.apply_btn.setEnabled(True)
        self.model_combo.addItems(self._model_cache)
        saved = settings_store.load(self.controller.hema.config.data_dir)
        current = self.controller.hema.assistant.models.current or saved.get("model")
        index = self.model_combo.findText(current or "")
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        self.status.setText("Active model: " +
                            (self.controller.hema.assistant.models.current or "not selected") +
                            f"  |  {len(self._model_cache)} installed")

    def apply_model(self):
        name = self.model_combo.currentText()
        if name not in self._model_cache:
            self.status.setText("Pick an installed model from the list first (Reconnect to refresh).")
            return
        saved = settings_store.load(self.controller.hema.config.data_dir)
        try:
            used = self.controller.use_model(name)
        except Exception as e:
            self.status.setText(f"Could not switch model: {e}")
            return
        settings_store.save(self.controller.hema.config.data_dir,
                            {"model": used, "ui_model": saved.get("ui_model", used)})
        self.status.setText(f"Now using {used} (saved for next start)")

    def save_settings(self):
        values = {"timeout": self.timeout_spin.value(),
                  "ui_model": self.model_combo.currentText() or self.controller.ui_model()}
        path = settings_store.save(self.controller.hema.config.data_dir, values)
        self.status.setText(f"Saved to {path}. Timeout applies to new requests.")

    def save_identity(self):
        from core.identity import IdentityError
        try:
            data = self.controller.set_identity(
                assistant_name=self.assistant_name_edit.text(),
                user_name=self.user_name_edit.text())
        except IdentityError as exc:
            self.identity_status.setText(f"Not saved: {exc}")
            return
        window = self.window()
        if hasattr(window, "apply_identity"):
            window.apply_identity()
        self.user_name_edit.setText(data["user_name"])
        self.assistant_name_edit.setText(data["assistant_name"])
        self.identity_status.setText(
            f"Saved. You are {data['user_name']} and I am {data['assistant_name']}.")

    def reconnect(self):
        self.refresh()
        hema = self.controller.hema
        hema.audit.record("reconnect", self.controller.ollama_host(), "requested")
