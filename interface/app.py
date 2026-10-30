"""HEMA desktop interface (PySide6). Run: python main.py --gui

Chat, model select, task list, memory, activity log, approvals, Dragon Tiger tab.
"""
import sys

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QMainWindow, QMessageBox,
                               QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget)

from interface.controller import HemaController


class ChatWorker(QThread):
    chunk = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, controller: HemaController, text: str):
        super().__init__()
        self.controller = controller
        self.text = text

    def run(self):
        try:
            for piece in self.controller.ask(self.text):
                self.chunk.emit(piece)
            self.finished_ok.emit()
        except Exception as e:
            self.failed.emit(str(e))


class ApprovalDialog(QDialog):
    """Polls the queue approver and lets the user approve or deny."""

    def __init__(self, controller: HemaController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("HEMA approval requested")
        self.resize(600, 300)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("HEMA is waiting for permission:"))
        self.list = QListWidget()
        layout.addWidget(self.list)
        row = QHBoxLayout()
        allow = QPushButton("Allow selected")
        deny = QPushButton("Deny selected")
        refresh = QPushButton("Refresh")
        row.addWidget(allow)
        row.addWidget(deny)
        row.addWidget(refresh)
        layout.addLayout(row)
        allow.clicked.connect(lambda: self._decide(True))
        deny.clicked.connect(lambda: self._decide(False))
        refresh.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for item in self.controller.pending_approvals():
            self.list.addItem(f"#{item['id']}  {item['action']}: {item['detail']}")
            self.list.item(self.list.count() - 1).setData(0x0100, item["id"])
        if self.list.count() == 0:
            self.list.addItem("(no pending requests)")

    def _decide(self, allow: bool):
        item = self.list.currentItem()
        if not item:
            return
        rid = item.data(0x0100)
        if rid:
            self.controller.decide_approval(rid, allow)
        self.refresh()


class MainWindow(QMainWindow):
    def __init__(self, controller: HemaController):
        super().__init__()
        self.controller = controller
        self.worker = None
        self.setWindowTitle("HEMA - Local AI Assistant")
        self.resize(1000, 720)

        central = QWidget()
        layout = QVBoxLayout(central)
        self.status = QLabel(controller.status_text())
        layout.addWidget(self.status)

        row = QHBoxLayout()
        self.model_box = QComboBox()
        self.model_box.addItems(controller.models() or ["(no models found)"])
        self.model_box.activated.connect(self._select_model)
        row.addWidget(QLabel("Model:"))
        row.addWidget(self.model_box)
        self.approval_btn = QPushButton("Approvals")
        self.approval_btn.clicked.connect(self._show_approvals)
        row.addWidget(self.approval_btn)
        self.model_swap = row
        layout.addLayout(row)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._chat_tab(), "Chat")
        self.tabs.addTab(self._list_tab("Tasks", "Refresh tasks", self._render_tasks), "Tasks")
        self.tabs.addTab(self._list_tab("Memory", "Refresh memory", self._render_memory), "Memory")
        self.tabs.addTab(self._list_tab("Log", "Refresh log", self._render_log), "Activity log")
        dt = QWidget()
        dtl = QVBoxLayout(dt)
        self.dt_view = QPlainTextEdit()
        self.dt_view.setReadOnly(True)
        dtl.addWidget(self.dt_view)
        dtl.addWidget(self._button("Refresh", lambda: self.dt_view.setPlainText(self.controller.dt_report())))
        self.tabs.addTab(dt, "Dragon Tiger")
        self.tabs.currentChanged.connect(lambda _: self._refresh_current())
        layout.addWidget(self.tabs)
        self.setCentralWidget(central)
        self._render_tasks()

    # --- widgets -------------------------------------------------
    def _button(self, label, slot) -> QPushButton:
        b = QPushButton(label)
        b.clicked.connect(slot)
        return b

    def _chat_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.chat_view = QPlainTextEdit()
        self.chat_view.setReadOnly(True)
        v.addWidget(self.chat_view)
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command for HEMA...")
        self.input.returnPressed.connect(self._send)
        row.addWidget(self.input)
        row.addWidget(self._button("Send", self._send))
        self.stop_btn = self._button("Stop", self._stop)
        row.addWidget(self.stop_btn)
        v.addLayout(row)
        return w

    def _list_tab(self, name: str, label: str, slot) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        lst = QListWidget()
        v.addWidget(lst)
        v.addWidget(self._button(label, slot))
        setattr(self, f"{name.lower()}_list", lst)
        return w

    # --- actions ------------------------------------------------
    def _send(self):
        text = self.input.text().strip()
        if not text or (self.worker and self.worker.isRunning()):
            return
        self.input.clear()
        self.chat_view.appendPlainText(f"You: {text}")
        self.chat_view.appendPlainText("HEMA: ")
        self.worker = ChatWorker(self.controller, text)
        self.worker.chunk.connect(lambda c: self.chat_view.insertPlainText(c))
        self.worker.finished_ok.connect(lambda: self.chat_view.appendPlainText(""))
        self.worker.failed.connect(lambda e: self.chat_view.appendPlainText(f"\n[error] {e}"))
        self.worker.start()

    def _stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(2000)

    def _select_model(self, index: int):
        name = self.model_box.itemText(index)
        try:
            self.controller.select_model(name)
            self.status.setText(self.controller.status_text())
        except Exception as e:
            QMessageBox.warning(self, "Model error", str(e))

    def _show_approvals(self):
        ApprovalDialog(self.controller, self).exec()

    def _render_tasks(self):
        self.tasks_list.clear()
        for t in self.controller.tasks():
            self.tasks_list.addItem(f"#{t.id} [{t.status}] {t.progress}% {t.description[:70]}")

    def _render_memory(self):
        self.memory_list.clear()
        for m in self.controller.memories():
            self.memory_list.addItem(f"#{m['id']} [{m['kind']}] {m['content'][:80]}")

    def _render_log(self):
        self.log_list.clear()
        for e in self.controller.audit_tail(100):
            self.log_list.addItem(f"{e['time']} {e['action']} -> {e['outcome']} ({e['detail'][:60]})")

    def _refresh_current(self):
        index = self.tabs.currentIndex()
        if index == 1:
            self._render_tasks()
        elif index == 2:
            self._render_memory()
        elif index == 3:
            self._render_log()
        elif index == 4:
            self.dt_view.setPlainText(self.controller.dt_report())

    def closeEvent(self, event):
        self._stop()
        self.controller.hema.close()
        super().closeEvent(event)


def run_gui(controller: HemaController) -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(controller)
    window.show()
    return app.exec()
