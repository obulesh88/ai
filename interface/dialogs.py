"""Glass-styled Tools dialog (Settings and Memory are full pages in the dashboard)."""
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
