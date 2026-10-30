"""Glass-styled dialogs: Settings, Memory, Tools."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QGridLayout, QHBoxLayout, QLabel,
                               QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget)

from interface import theme
from interface.widgets import GlassPanel


def _kv(label: str, value: str) -> QWidget:
    row = QWidget()
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 0, 0, 0)
    k = QLabel(label.upper())
    k.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:10px; letter-spacing:1px;")
    k.setMinimumWidth(120)
    v = QLabel(value)
    v.setStyleSheet(f"color:{theme.TEXT}; font-family:Consolas, monospace;")
    v.setTextInteractionFlags(Qt.TextSelectableByMouse)
    h.addWidget(k)
    h.addWidget(v, 1)
    return row


class SettingsDialog(QDialog):
    """Shows the active model and Ollama URL, and lets the model be switched."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("HEMA Settings")
        self.resize(560, 400)
        self.setStyleSheet(theme.stylesheet())

        root = QVBoxLayout(self)
        panel = GlassPanel("Connection")
        self.model_label = QLabel()
        panel.add(_kv("Ollama URL", controller.ollama_host()))
        panel.add(_kv("Active model", controller.hema.assistant.models.current or "(not connected)"))
        panel.add(_kv("Preferred (UI)", controller.ui_model()))
        panel.add(_kv("Workspace", controller.workspace_path()))
        panel.add(_kv("Config file", ".env (optional)"))
        root.addWidget(panel)

        switcher = GlassPanel("Switch model")
        row = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setMinimumWidth(260)
        self.refresh_btn = QPushButton("Refresh list")
        self.apply_btn = QPushButton("Use this model")
        self.apply_btn.setObjectName("SendButton")
        row.addWidget(self.combo, 1)
        row.addWidget(self.refresh_btn)
        row.addWidget(self.apply_btn)
        switcher.add_layout(row)
        self.note = QLabel("Model settings are applied for this session only. "
                           "To make them permanent, edit .env (HEMA_MODEL).")
        self.note.setWordWrap(True)
        self.note.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px;")
        switcher.add(self.note)
        root.addWidget(switcher)
        root.addStretch(1)

        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(close)
        root.addLayout(bottom)

        self.refresh_btn.clicked.connect(self.refresh)
        self.apply_btn.clicked.connect(self.apply_model)
        self.refresh()

    def refresh(self):
        self.combo.clear()
        models = self.controller.models()
        if not models:
            self.combo.addItem("Ollama unreachable - start 'ollama serve'")
            self.combo.setEnabled(False)
            self.apply_btn.setEnabled(False)
            return
        self.combo.setEnabled(True)
        self.apply_btn.setEnabled(True)
        self.combo.addItems(models)
        current = self.controller.hema.assistant.models.current
        preferred = current or self.controller.ui_model()
        idx = self.combo.findText(preferred)
        if idx < 0 and ":" not in preferred:
            idx = self.combo.findText(preferred + ":latest")
        self.combo.setCurrentIndex(max(0, idx))

    def apply_model(self):
        name = self.combo.currentText()
        try:
            self.controller.select_model(name)
            QMessageBox.information(self, "Model switched", f"HEMA is now using {name}.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Could not switch model", str(e))


class MemoryDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("HEMA Memory")
        self.resize(620, 460)
        self.setStyleSheet(theme.stylesheet())
        root = QVBoxLayout(self)
        panel = GlassPanel("Stored memories")
        self.list = QListWidget()
        panel.add(self.list, 1)
        row = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.delete_btn = QPushButton("Delete selected")
        row.addWidget(self.refresh_btn)
        row.addStretch(1)
        row.addWidget(self.delete_btn)
        panel.add_layout(row)
        root.addWidget(panel)
        self.refresh_btn.clicked.connect(self.refresh)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.refresh()

    def refresh(self):
        self.list.clear()
        rows = self.controller.memories()
        if not rows:
            item_text = "(no memories yet - say 'remember: ...' in chat)"
            self.list.addItem(item_text)
            return
        for m in rows:
            self.list.addItem(f"#{m['id']}  [{m['kind']}]  {m['content']}")
            self.list.item(self.list.count() - 1).setData(Qt.UserRole, m["id"])

    def delete_selected(self):
        item = self.list.currentItem()
        mid = item.data(Qt.UserRole) if item else None
        if not mid:
            return
        answer = QMessageBox.question(self, "Delete memory",
                                      f"Delete memory #{mid}? This cannot be undone.")
        if answer != QMessageBox.Yes:
            return
        self.controller.delete_memory_confirmed(int(mid))
        self.refresh()


class ToolsDialog(QDialog):
    """Lists real capabilities: command patterns and MCP server status."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HEMA Tools")
        self.resize(700, 520)
        self.setStyleSheet(theme.stylesheet())
        root = QVBoxLayout(self)

        commands = GlassPanel("Natural-language commands")
        clist = QListWidget()
        for kind, pattern in controller.known_commands():
            clist.addItem(f"{kind:16s}  {pattern}")
        commands.add(clist, 1)
        root.addWidget(commands, 3)

        mcp = GlassPanel("MCP servers")
        mlist = QListWidget()
        servers = controller.mcp_servers()
        if not servers:
            mlist.addItem("No MCP servers configured (set HEMA_MCP_CONFIG in .env)")
        for s in servers:
            state = "ready" if s["command_found"] else "command not found"
            mlist.addItem(f"{s['name']}: {s['command']} {s['args']} -> {state}")
        mcp.add(mlist, 1)
        root.addWidget(mcp, 2)

        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(close)
        root.addLayout(bottom)
