"""GUI tests for the HEMA dashboard. Run offscreen, or on a normal desktop directly.

In a headless sandbox:  QT_QPA_PLATFORM=offscreen python -m unittest tests.test_ui
"""
import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from config import Config
from core.hema import Hema
from interface import settings_store
from interface.controller import HemaController
from security.permissions import QueueApprover
from tests.fake_ollama import start_server


def qt_available():
    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401
        return True, ""
    except Exception as e:  # ImportError or missing system libs
        return False, str(e)


AVAILABLE, REASON = qt_available()


@unittest.skipUnless(AVAILABLE, f"PySide6 not usable: {REASON}")
class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        from interface import theme
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        cls.app.setPalette(theme.palette())
        cls.app.setStyleSheet(theme.stylesheet())

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.server, self.url, self.state = start_server(("qwen3.5:2b", "qwen3-coder-local:latest"))
        self.addCleanup(self.server.shutdown)
        self.window = None

    def make_window(self, host=None):
        from interface.main_window import MainWindow
        config = Config(host or self.url, "qwen3-coder-local:latest", 10.0, 20, "sys",
                        workspace_dir=self.root / "ws", data_dir=self.root / "data",
                        logs_dir=self.root / "logs", backups_dir=self.root / "bk",
                        ui_model="qwen3.5:2b")
        hema = Hema(config, QueueApprover(timeout=5))
        self.addCleanup(self._close_hema, hema)
        window = MainWindow(HemaController(hema))
        window.show()
        self.window = window
        self.addCleanup(window.close)
        return window

    @staticmethod
    def _close_hema(hema):
        try:
            hema.close()
        except Exception:
            pass

    def pump(self, seconds: float, until=None):
        end = time.time() + seconds
        while time.time() < end:
            self.app.processEvents()
            if until and until():
                return True
            time.sleep(0.02)
        return False

    def connected(self, window, timeout: float = 10.0) -> bool:
        return self.pump(timeout, lambda: "ONLINE" in window.conn_pill.text())

    def send(self, window, text: str, timeout: float = 20.0) -> str:
        window.input.setText(text)
        window.send_message()
        self.pump(timeout, lambda: window.worker is not None and window.worker.isFinished())
        self.pump(0.3)
        return window.chat.transcript()

    # ---------------------------------------------------------------- layout
    def test_dashboard_structure(self):
        w = self.make_window()
        self.pump(0.4)
        self.assertEqual(len(w.nav_buttons), 8)
        self.assertEqual([w.stack.widget(i).__class__.__name__ for i in range(8)],
                         ["ChatPage", "HistoryPage", "GameDevPage", "UnityPage",
                          "UnrealPage", "MemoryPage", "TasksPage", "SettingsPage"])
        self.assertTrue(w.greeting.isVisible())
        self.assertFalse(w.banner.isVisible())
        for meter in (w.meter_cpu, w.meter_mem, w.meter_disk):
            self.assertGreater(meter.height(), 10)
        self.assertGreaterEqual(w.minimumWidth(), 1100)

    def test_sidebar_navigation_switches_pages(self):
        w = self.make_window()
        for key in ("history", "game", "unity", "unreal", "memory", "tasks", "settings", "chat"):
            w.goto(key)
            self.pump(0.1)
            self.assertEqual(w.current_page_key(), key)
            self.assertTrue(w.nav_buttons[key].isChecked())
            others = [k for k, b in w.nav_buttons.items() if k != key and b.isChecked()]
            self.assertEqual(others, [])

    # ------------------------------------------------------------------ chat
    def test_real_chat_roundtrip(self):
        w = self.make_window()
        self.assertTrue(self.connected(w))
        self.assertIn("qwen3.5:2b", w.model_chip.toolTip() or w.model_chip.text())
        transcript = self.send(w, "hello")
        self.assertIn("hello", transcript)
        self.assertIn("reply", transcript)
        self.assertEqual(len(self.state["requests"]), 1)
        self.assertEqual(self.state["requests"][0]["model"], "qwen3.5:2b")
        self.assertFalse(w.greeting.isVisible())
        self.assertTrue(w.send_btn.isEnabled())
        self.assertEqual(w.status_dot._state, "online")

    def test_streaming_is_incremental(self):
        w = self.make_window()
        self.connected(w)
        seen = []
        original = w._on_chunk
        w._on_chunk = lambda text: (seen.append(text), original(text))
        self.send(w, "hi")
        self.assertGreaterEqual(len(seen), 2)

    def test_messages_keep_their_order(self):
        w = self.make_window()
        self.connected(w)
        for text in ("first", "second", "third"):
            w.input.setText(text)
            w.send_message()
            self.pump(15, lambda: not w._busy)
            self.pump(0.15)
        transcript = " ".join(w.chat.transcript().split())
        self.assertLess(transcript.index("first"), transcript.index("reply1"))
        self.assertLess(transcript.index("reply1"), transcript.index("second"))
        self.assertLess(transcript.index("second"), transcript.index("reply2"))
        self.assertLess(transcript.index("reply2"), transcript.index("third"))

    def test_typing_while_busy_keeps_the_text(self):
        w = self.make_window()
        self.connected(w)
        w.input.setText("hello")
        w.send_message()
        self.assertTrue(w._busy)
        # a second send while busy must not lose the message nor interleave
        w.input.setText("second message")
        w.send_message()
        self.assertEqual(w.input.text(), "second message")
        self.pump(15, lambda: not w._busy)
        self.pump(0.2)
        self.assertEqual(w.input.text(), "second message")
        transcript = " ".join(w.chat.transcript().split())
        self.assertNotIn("second message", transcript)

    def test_clear_chat_restores_greeting(self):
        w = self.make_window()
        self.connected(w)
        self.send(w, "hello")
        self.assertFalse(w.greeting.isVisible())
        w.clear_chat()
        self.pump(0.2)
        self.assertTrue(w.greeting.isVisible())
        self.assertTrue(w.chat.is_empty())

    def test_offline_state_is_clear(self):
        w = self.make_window(host="http://127.0.0.1:1")
        self.assertTrue(self.pump(12, lambda: "OFFLINE" in w.conn_pill.text()))
        self.assertEqual(w.status_dot._state, "offline")
        self.assertEqual(w.avatar.state, "error")
        self.assertIn("unreachable", w.chat.transcript().lower())
        self.assertIn("unreachable", w.rail_status.text().lower())

    # ---------------------------------------------------------- engine actions
    def test_memory_command_updates_rail_and_page(self):
        w = self.make_window()
        self.connected(w)
        self.send(w, "remember: I use Unity 2022")
        self.assertIn("1 memory", w.rail_memory.text())
        w.goto("memory")
        self.pump(0.2)
        self.assertIn("I use Unity 2022", w.page_memory.list.item(0).text())

    def test_tasks_page_shows_plan(self):
        w = self.make_window()
        self.connected(w)
        self.send(w, "plan: make a pong game")
        w.goto("tasks")
        self.pump(0.2)
        self.assertGreater(w.page_tasks.list.count(), 0)
        self.assertIn("pending", w.page_tasks.list.item(0).text())

    def test_approval_banner_denies_command(self):
        w = self.make_window()
        self.connected(w)
        w.input.setText("run: echo should-not-run")
        w.send_message()
        self.assertTrue(self.pump(12, lambda: w.banner.isVisible()))
        self.assertIn("run-command", w.banner_label.text())
        w._decide_approval(False)
        self.pump(1.2)
        self.assertIn("Not permitted", w.chat.transcript())

    # -------------------------------------------------------------- settings
    def test_settings_page_lists_models_and_saves(self):
        w = self.make_window()
        self.connected(w)
        w.goto("settings")
        self.assertTrue(self.pump(8, lambda: w.page_settings.model_combo.count() > 0
                                  and "qwen3.5:2b" in w.page_settings.model_combo.itemText(0)))
        page = w.page_settings
        page.timeout_spin.setValue(42)
        page.save_btn.click()
        saved = settings_store.load(w.controller.hema.config.data_dir)
        self.assertEqual(float(saved["timeout"]), 42.0)
        page.model_combo.setCurrentText("qwen3-coder-local:latest")
        page.apply_model()
        self.assertEqual(w.controller.hema.assistant.models.current, "qwen3-coder-local:latest")
        self.assertEqual(settings_store.load(w.controller.hema.config.data_dir)["model"],
                         "qwen3-coder-local:latest")

    def test_no_widget_overflows_at_minimum_window_size(self):
        w = self.make_window()
        self.connected(w)
        self.send(w, "remember: I build games in Unity 2022")
        w.resize(w.minimumWidth(), w.minimumHeight())
        self.pump(0.6)
        # chat transcript must end above the composer inside its own panel
        chat_bottom = w.chat.mapTo(w, w.chat.rect().bottomLeft()).y()
        input_top = w.input.mapTo(w, w.input.rect().topLeft()).y()
        self.assertLessEqual(chat_bottom, input_top,
                             f"chat overlaps composer: {chat_bottom} > {input_top}")
        # sidebar, workspace and rail must not overlap horizontally
        rail_left = w.meter_cpu.mapTo(w, w.meter_cpu.rect().topLeft()).x()
        stack_right = w.stack.mapTo(w, w.stack.rect().topRight()).x()
        self.assertLessEqual(stack_right, rail_left)
        for widget in (w.send_btn, w.stop_btn, w.greeting, w.meter_cpu):
            point = widget.mapTo(w, widget.rect().bottomRight())
            self.assertLessEqual(point.y(), w.height())
            self.assertLessEqual(point.x(), w.width())

    def test_saved_settings_are_applied_on_restart(self):
        w = self.make_window()
        self.connected(w)
        settings_store.save(w.controller.hema.config.data_dir,
                            {"model": "qwen3-coder-local:latest", "timeout": 33})
        w.close()
        w2 = self.make_window()
        self.assertTrue(self.pump(10, lambda: "ONLINE" in w2.conn_pill.text()))
        self.assertEqual(w2.controller.hema.assistant.models.current, "qwen3-coder-local:latest")
        self.assertEqual(w2.controller.hema.assistant.client.timeout, 33.0)

    # ------------------------------------------------------------- screenshots
    def test_screenshot(self):
        w = self.make_window()
        self.connected(w)
        self.send(w, "remember: I am learning Unreal Engine 5")
        self.send(w, "hello HEMA")
        self.pump(0.6)
        out_dir = Path(__file__).resolve().parent.parent / "docs"
        out_dir.mkdir(exist_ok=True)
        path = out_dir / "hema-ui.png"
        self.assertTrue(w.grab().save(str(path)))
        self.assertGreater(path.stat().st_size, 5000)


if __name__ == "__main__":
    unittest.main()
