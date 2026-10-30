"""HEMA futuristic main window."""
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QMainWindow, QMessageBox, QProgressBar,
                               QPushButton, QSizePolicy, QTabWidget, QTextEdit,
                               QVBoxLayout, QWidget)

from interface import system_stats, theme
from interface.dialogs import MemoryDialog, SettingsDialog, ToolsDialog
from interface.widgets import ChatView, GlassPanel, HoloAvatar, QuickTile, StatGauge

MONO = f"font-family: {theme.FONT_MONO};"
NETWORK_SCALE_BPS = 10 * 1024 * 1024  # NETWORK arc = total throughput relative to 10 MB/s


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

    result = Signal(bool, str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        try:
            models = self.controller.models()
            if not models:
                self.result.emit(False, "Ollama unreachable at " + self.controller.ollama_host())
                return
            self.result.emit(True, f"{len(models)} model(s) available")
        except Exception as e:
            self.result.emit(False, str(e))


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.worker = None
        self._last_log_pos = 0
        self._pending_id = None

        self.setWindowTitle("HEMA AI - Local Neural Assistant")
        self.resize(1440, 900)
        self.setMinimumSize(1120, 720)

        root = QWidget()
        root.setObjectName("RootBackground")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 12, 16, 8)
        outer.setSpacing(10)
        outer.addLayout(self._build_header())
        outer.addWidget(self._build_approval_banner())

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._build_left_column(), 0)
        body.addWidget(self._build_center_column(), 1)
        body.addWidget(self._build_right_column(), 0)
        outer.addLayout(body, 1)
        self.setCentralWidget(root)

        self.statusBar().showMessage("Starting HEMA...")
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start(1500)
        self._log_timer = QTimer(self)
        self._log_timer.timeout.connect(self._poll_logs)
        self._log_timer.start(1200)
        self._approval_timer = QTimer(self)
        self._approval_timer.timeout.connect(self._poll_approvals)
        self._approval_timer.start(500)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)

        self._update_stats()
        self._render_tasks()
        self._render_memory()
        QTimer.singleShot(200, self._probe_connection)

    # ------------------------------------------------------------------ header
    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("HEMA AI")
        title.setObjectName("AppTitle")
        sub = QLabel("LOCAL NEURAL ASSISTANT  //  SEGMENT 2")
        sub.setObjectName("AppSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch(1)

        self.conn_pill = QLabel("CONNECTING...")
        self.conn_pill.setObjectName("StatusPill")
        self.model_pill = QLabel("MODEL: -")
        self.model_pill.setObjectName("StatusPill")
        self.url_pill = QLabel(self.controller.ollama_host())
        self.url_pill.setObjectName("StatusPill")
        self.clock_pill = QLabel("--:--:--")
        self.clock_pill.setObjectName("StatusPill")
        for w in (self.conn_pill, self.model_pill, self.url_pill, self.clock_pill):
            header.addWidget(w)
        self._tick_clock()
        return header

    def _build_approval_banner(self) -> QWidget:
        self.banner = QWidget()
        row = QHBoxLayout(self.banner)
        row.setContentsMargins(0, 0, 0, 0)
        self.banner_label = QLabel("")
        self.banner_label.setObjectName("ApprovalBanner")
        self.banner_label.setWordWrap(True)
        allow = QPushButton("Allow")
        allow.setObjectName("SendButton")
        deny = QPushButton("Deny")
        allow.clicked.connect(lambda: self._decide_approval(True))
        deny.clicked.connect(lambda: self._decide_approval(False))
        row.addWidget(self.banner_label, 1)
        row.addWidget(allow)
        row.addWidget(deny)
        self.banner.setVisible(False)
        return self.banner

    # ------------------------------------------------------------- left column
    def _build_left_column(self) -> QWidget:
        col = QWidget()
        col.setFixedWidth(300)
        v = QVBoxLayout(col)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)

        quick = GlassPanel("Quick access")
        grid = QGridLayout()
        grid.setSpacing(8)
        tiles = (("\u25C9", "Memory", self._open_memory),
                 ("\u2699", "Settings", self._open_settings),
                 ("\u2611", "Tasks", self._focus_tasks),
                 ("\u26A1", "Tools", self._open_tools))
        for i, (icon, label, slot) in enumerate(tiles):
            tile = QuickTile(icon, label)
            tile.clicked.connect(slot)
            grid.addWidget(tile, i // 2, i % 2)
        quick.add_layout(grid)
        v.addWidget(quick)

        monitor = GlassPanel("System overview")
        gauges = QGridLayout()
        gauges.setSpacing(4)
        self.gauge_cpu = StatGauge("CPU")
        self.gauge_mem = StatGauge("MEMORY")
        self.gauge_disk = StatGauge("DISK")
        self.gauge_net = StatGauge("NETWORK", unit="", warn_at=None, danger_at=None)
        gauges.addWidget(self.gauge_cpu, 0, 0)
        gauges.addWidget(self.gauge_mem, 0, 1)
        gauges.addWidget(self.gauge_disk, 1, 0)
        gauges.addWidget(self.gauge_net, 1, 1)
        monitor.add_layout(gauges)
        v.addWidget(monitor, 1)

        self.dt_panel = GlassPanel("Dragon Tiger")
        self.dt_label = QLabel("no results recorded")
        self.dt_label.setWordWrap(True)
        self.dt_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.dt_label.setStyleSheet(f"{MONO} color:{theme.TEXT_DIM}; font-size:11px;")
        self.dt_panel.add(self.dt_label, 1)
        v.addWidget(self.dt_panel, 1)
        return col

    # ----------------------------------------------------------- center column
    def _build_center_column(self) -> QWidget:
        col = QWidget()
        v = QVBoxLayout(col)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)

        holo = GlassPanel("Holographic interface")
        self.avatar = HoloAvatar()
        holo.add(self.avatar, 1)
        v.addWidget(holo, 5)

        chat = GlassPanel("Conversation")
        self.chat = ChatView()
        chat.add(self.chat, 1)
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask HEMA anything, or give a command (try: /help)")
        self.input.returnPressed.connect(self.send_message)
        self.send_btn = QPushButton("SEND")
        self.send_btn.setObjectName("SendButton")
        self.send_btn.clicked.connect(self.send_message)
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setEnabled(False)
        row.addWidget(self.input, 1)
        row.addWidget(self.send_btn)
        row.addWidget(self.stop_btn)
        chat.add_layout(row)
        v.addWidget(chat, 7)
        return col

    # ------------------------------------------------------------ right column
    def _build_right_column(self) -> QWidget:
        col = QWidget()
        col.setFixedWidth(392)
        v = QVBoxLayout(col)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)

        self.right_tabs = QTabWidget()

        activity = QWidget()
        av = QVBoxLayout(activity)
        av.setContentsMargins(6, 6, 6, 6)
        self.activity_list = QListWidget()
        av.addWidget(self.activity_list)
        self.right_tabs.addTab(activity, "ACTIVITY")

        terminal = QWidget()
        tv = QVBoxLayout(terminal)
        tv.setContentsMargins(6, 6, 6, 6)
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont(theme.FONT_MONO, 9))
        tv.addWidget(self.terminal)
        self.right_tabs.addTab(terminal, "TERMINAL")

        tasks = QWidget()
        tsv = QVBoxLayout(tasks)
        tsv.setContentsMargins(6, 6, 6, 6)
        self.task_list = QListWidget()
        tsv.addWidget(self.task_list, 1)
        self.task_progress = QProgressBar()
        self.task_progress.setRange(0, 100)
        tsv.addWidget(self.task_progress)
        self.task_detail = QLabel("select a task to see its report")
        self.task_detail.setWordWrap(True)
        self.task_detail.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px;")
        tsv.addWidget(self.task_detail)
        self.task_list.currentItemChanged.connect(self._show_task_detail)
        self.right_tabs.addTab(tasks, "TASKS")

        memory = QWidget()
        mv = QVBoxLayout(memory)
        mv.setContentsMargins(6, 6, 6, 6)
        self.memory_list = QListWidget()
        mv.addWidget(self.memory_list)
        self.right_tabs.addTab(memory, "MEMORY")

        panel = GlassPanel("Diagnostics")
        panel.add(self.right_tabs, 1)
        v.addWidget(panel, 1)

        settings_row = GlassPanel("Model")
        srow = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.model_combo.activated.connect(self._choose_model)
        refresh = QPushButton("\u21BB")
        refresh.setToolTip("Refresh model list")
        refresh.clicked.connect(self._probe_connection)
        srow.addWidget(self.model_combo, 1)
        srow.addWidget(refresh)
        settings_row.add_layout(srow)
        v.addWidget(settings_row)
        return col

    # ------------------------------------------------------------------ timers
    def _tick_clock(self):
        self.clock_pill.setText(time.strftime("%H:%M:%S"))

    def _update_stats(self):
        s = system_stats.snapshot()
        self.gauge_cpu.set_value(s["cpu"], os_cpu_threads())
        mem_detail = (f"{system_stats.human_bytes(s['mem_used'])} / "
                      f"{system_stats.human_bytes(s['mem_total'])}")
        self.gauge_mem.set_value(s["mem_percent"], mem_detail)
        self.gauge_disk.set_value(s["disk_percent"],
                                  "free " + system_stats.human_bytes(s["disk_free"]))
        down = system_stats.human_bytes(s["down_bps"], "/s") if s["down_bps"] is not None else "n/a"
        up = system_stats.human_bytes(s["up_bps"], "/s") if s["up_bps"] is not None else "n/a"
        # the arc is relative to NETWORK_SCALE_BPS, not a percentage of capacity
        if s["down_bps"] is not None:
            net_pct = min(100.0, (s["down_bps"] + s["up_bps"]) / NETWORK_SCALE_BPS * 100)
            net_detail = f"\u2193{down} \u2191{up}"
        else:
            net_pct, net_detail = None, "n/a"
        self.gauge_net.set_value(net_pct, net_detail)
        try:
            report = self.controller.dt_report().splitlines()
            summary = [ln.strip() for ln in report if ln.strip().startswith(("Dragon", "Tiger", "Tie"))]
            self.dt_label.setText("\n".join(summary[:3]) if summary else "no results recorded")
        except Exception:
            self.dt_label.setText("statistics unavailable")

    def _poll_logs(self):
        self._render_activity()
        log_path = Path(self.controller.hema.config.logs_dir) / "hema.log"
        if not log_path.is_file():
            return
        try:
            size = log_path.stat().st_size
            if size < self._last_log_pos:
                self._last_log_pos = 0
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._last_log_pos)
                new = f.read()
                self._last_log_pos = f.tell()
        except OSError:
            return
        for line in new.splitlines()[-30:]:
            self.terminal.append(f"<span style='color:{theme.TEXT_DIM}'>{line}</span>")

    def _render_activity(self):
        entries = self.controller.audit_tail(60)
        self.activity_list.clear()
        if not entries:
            self.activity_list.addItem("(no activity yet)")
        for e in reversed(entries):
            color = theme.OK if e["outcome"].startswith("approved") else theme.WARN
            if "denied" in e["outcome"]:
                color = theme.DANGER
            self.activity_list.addItem(f"{e['time'][11:]}  {e['action']}  [{e['outcome']}]")
            self.activity_list.item(self.activity_list.count() - 1).setForeground(Qt.gray)
            self.activity_list.item(self.activity_list.count() - 1).setToolTip(
                f"{e['detail']} ({color})")

    def _poll_approvals(self):
        pending = self.controller.pending_approvals()
        if not pending:
            if self.banner.isVisible():
                self.banner.setVisible(False)
                self._pending_id = None
            return
        first = pending[0]
        self._pending_id = first["id"]
        self.banner_label.setText(
            f"HEMA needs permission - {first['action']}: {first['detail']}")
        self.banner.setVisible(True)

    def _decide_approval(self, allow: bool):
        if self._pending_id is None:
            return
        self.controller.decide_approval(self._pending_id, allow)
        self.terminal.append(f"<span style='color:{theme.WARN}'>[approval] id={self._pending_id} "
                            f"{'allowed' if allow else 'denied'}</span>")
        self._pending_id = None
        self.banner.setVisible(False)

    # ------------------------------------------------------------------- chat
    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return
        if self.worker and self.worker.isRunning():
            return
        self.input.clear()
        self.chat.add("user", text)
        self.chat.begin_stream()
        self.avatar.set_state("thinking")
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage("HEMA is processing...")
        self.worker = ChatWorker(self.controller, text)
        self.worker.chunk.connect(self._on_chunk)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_chunk(self, text: str):
        self.chat.append_stream(text)

    def _on_done(self):
        final = self.chat.end_stream()
        self._finish_request()
        lowered = final.lower()
        if "ollama error" in lowered or "permissiondenied" in lowered or "not approved" in lowered:
            self.avatar.set_state("error")
            self.statusBar().showMessage("Request failed - see the message above")
        else:
            self.avatar.set_state("idle")
            self.statusBar().showMessage("Ready")
        self._render_tasks()
        self._render_memory()

    def _on_failed(self, message: str):
        self.chat.end_stream()
        self.chat.add("error", message)
        self.avatar.set_state("error")
        self._finish_request()
        self.statusBar().showMessage("Error: " + message)
        self.terminal.append(f"<span style='color:{theme.DANGER}'>[error] {message}</span>")

    def _finish_request(self):
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input.setFocus()

    def stop_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(3000)
            self.chat.end_stream(" [stopped]")
            self.avatar.set_state("idle")
            self._finish_request()
            self.statusBar().showMessage("Stopped by user")

    # -------------------------------------------------------------- connection
    def _probe_connection(self):
        self.conn_pill.setText("CONNECTING...")
        self.probe = ProbeWorker(self.controller)
        self.probe.result.connect(self._on_probe)
        self.probe.start()

    def _on_probe(self, ok: bool, message: str):
        if ok:
            models = self.controller.models()
            self.model_combo.clear()
            self.model_combo.addItems(models)
            current = self.controller.hema.assistant.models.current
            if not current and models:
                preferred = self.controller.ui_model()
                pick = preferred if preferred in models else (
                    preferred + ":latest" if preferred + ":latest" in models else models[0])
                try:
                    current = self.controller.select_model(pick)
                except Exception:
                    current = models[0]
            idx = self.model_combo.findText(current or "")
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            self.conn_pill.setText("\u25CF ONLINE")
            self.conn_pill.setStyleSheet(f"color:{theme.OK}; border:1px solid {theme.OK};"
                                         f"border-radius:10px; padding:4px 10px; font-size:11px;")
            self.model_pill.setText(f"MODEL: {current or '-'}")
            self.statusBar().showMessage(f"Connected - {message}")
            self.avatar.set_state("idle")
        else:
            self.conn_pill.setText("\u25CF OFFLINE")
            self.conn_pill.setStyleSheet(f"color:{theme.DANGER}; border:1px solid {theme.DANGER};"
                                         f"border-radius:10px; padding:4px 10px; font-size:11px;")
            self.statusBar().showMessage(message)
            self.terminal.append(f"<span style='color:{theme.DANGER}'>[connection] {message}</span>")
            self.chat.add("error", message + "\nStart Ollama, then press the refresh button next to the model list.")
            self.avatar.set_state("error")

    def _choose_model(self, index: int):
        name = self.model_combo.itemText(index)
        try:
            used = self.controller.select_model(name)
            self.model_pill.setText(f"MODEL: {used}")
            self.terminal.append(f"<span style='color:{theme.CYAN}'>[model] switched to {used}</span>")
        except Exception as e:
            self.chat.add("error", f"Could not switch model: {e}")

    # ------------------------------------------------------------------ panels
    def _render_tasks(self):
        self.task_list.clear()
        rows = self.controller.tasks()
        if not rows:
            self.task_list.addItem("(no tasks yet - try 'plan: <something>')")
        for t in rows:
            verified = "verified" if t.verified else t.status
            self.task_list.addItem(f"#{t.id}  [{verified}]  {t.description[:52]}")
            item = self.task_list.item(self.task_list.count() - 1)
            item.setData(Qt.UserRole, (t.id, t.progress, t.report or "(no report yet)"))

    def _show_task_detail(self, current, previous=None):
        if current is None:
            return
        _, progress, report = current.data(Qt.UserRole)
        self.task_progress.setValue(int(progress))
        self.task_detail.setText(report)

    def _render_memory(self):
        self.memory_list.clear()
        rows = self.controller.memories()
        if not rows:
            self.memory_list.addItem("(empty)")
        for m in rows[-40:]:
            self.memory_list.addItem(f"#{m['id']} [{m['kind']}] {m['content'][:60]}")

    def _focus_tasks(self):
        self.right_tabs.setCurrentIndex(2)
        self._render_tasks()

    def _open_memory(self):
        MemoryDialog(self.controller, self).exec()
        self._render_memory()

    def _open_settings(self):
        SettingsDialog(self.controller, self).exec()
        current = self.controller.hema.assistant.models.current
        self.model_pill.setText(f"MODEL: {current or '-'}")

    def _open_tools(self):
        ToolsDialog(self.controller, self).exec()

    # ------------------------------------------------------------------ close
    def closeEvent(self, event):
        for timer in (self._stats_timer, self._log_timer, self._approval_timer, self._clock_timer):
            timer.stop()
        for thread in (self.worker, getattr(self, "probe", None)):
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


def os_cpu_threads() -> str:
    import os
    return f"{os.cpu_count() or 1} threads"
