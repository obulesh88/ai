"""GUI tests. They run offscreen; skip cleanly when PySide6 or Qt libs are missing.

On a normal desktop run:  python -m unittest tests.test_ui
In a headless sandbox:    QT_QPA_PLATFORM=offscreen python -m unittest tests.test_ui
"""
import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from config import Config
from core.hema import Hema
from interface.controller import HemaController
from security.permissions import QueueApprover
from tests.fake_ollama import start_server


def qt_available():
    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401
        return True, ""
    except Exception as e:  # ImportError or missing libEGL
        return False, str(e)

AVAILABLE, REASON = qt_available()


@unittest.skipUnless(AVAILABLE, f"PySide6 not usable: {REASON}")
class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        from interface import theme
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.stylesheet())

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.server, self.url, self.state = start_server(("qwen3.5:2b", "qwen3-coder-local:latest"))
        self.addCleanup(self.server.shutdown)

    def make_window(self, host=None):
        from interface.main_window import MainWindow
        config = Config(host or self.url, "qwen3-coder-local:latest", 10.0, 20, "sys",
                        workspace_dir=self.root / "ws", data_dir=self.root / "data",
                        logs_dir=self.root / "logs", backups_dir=self.root / "bk",
                        ui_model="qwen3.5:2b")
        hema = Hema(config, QueueApprover(timeout=5))
        self.addCleanup(hema.close)
        window = MainWindow(HemaController(hema))
        window.show()
        self.addCleanup(window.close)
        return window

    def pump(self, seconds: float, until=None):
        end = time.time() + seconds
        while time.time() < end:
            self.app.processEvents()
            if until and until():
                return True
            time.sleep(0.02)
        return False

    def test_window_builds_with_all_panels(self):
        w = self.make_window()
        self.pump(0.4)
        self.assertTrue(w.avatar is not None)
        self.assertEqual(w.right_tabs.count(), 4)
        self.assertEqual([w.right_tabs.tabText(i) for i in range(4)],
                         ["ACTIVITY", "TERMINAL", "TASKS", "MEMORY"])
        self.assertFalse(w.banner.isVisible())
        self.assertGreater(w.width(), 1000)

    def test_real_chat_gets_reply_from_engine(self):
        w = self.make_window()
        self.assertTrue(self.pump(8, lambda: "ONLINE" in w.conn_pill.text()), "never connected")
        self.assertIn("qwen3.5:2b", w.model_pill.text())
        w.input.setText("hello")
        w.send_message()
        self.assertTrue(self.pump(15, lambda: w.worker and w.worker.isFinished()), "no reply")
        self.pump(0.3)
        transcript = w.chat.transcript()
        self.assertIn("hello", transcript)
        self.assertIn("reply", transcript)          # text produced by the engine
        self.assertEqual(w.avatar.state, "idle")
        self.assertTrue(w.send_btn.isEnabled())
        # the request really reached the model API
        self.assertEqual(len([r for r in self.state["requests"]]), 1)
        self.assertEqual(self.state["requests"][0]["model"], "qwen3.5:2b")

    def test_streaming_is_incremental(self):
        w = self.make_window()
        self.pump(8, lambda: "ONLINE" in w.conn_pill.text())
        seen = []
        w.worker_chunks = []
        original = w._on_chunk
        w._on_chunk = lambda t: (seen.append(t), original(t))
        w.input.setText("hi")
        w.send_message()
        self.pump(15, lambda: w.worker and w.worker.isFinished())
        self.pump(0.2)
        self.assertGreaterEqual(len(seen), 2, "expected multiple streamed chunks")

    def test_offline_shows_clear_error(self):
        w = self.make_window(host="http://127.0.0.1:1")
        self.assertTrue(self.pump(10, lambda: "OFFLINE" in w.conn_pill.text()))
        self.assertEqual(w.avatar.state, "error")
        self.assertIn("unreachable", w.statusBar().currentMessage().lower())
        self.assertIn("Ollama unreachable", w.chat.transcript())

    def test_command_through_ui_runs_real_engine(self):
        w = self.make_window()
        self.pump(8, lambda: "ONLINE" in w.conn_pill.text())
        w.input.setText("remember: I use Unity 2022")
        w.send_message()
        self.pump(15, lambda: w.worker and w.worker.isFinished())
        self.pump(0.3)
        self.assertIn("Saved to memory", w.chat.transcript())
        self.assertIn("I use Unity 2022", w.memory_list.item(0).text())

    def test_approval_banner_appears_and_denies(self):
        w = self.make_window()
        self.pump(8, lambda: "ONLINE" in w.conn_pill.text())
        w.input.setText("run: echo should-not-run")
        w.send_message()
        self.assertTrue(self.pump(10, lambda: w.banner.isVisible()), "no approval banner")
        self.assertIn("run-command", w.banner_label.text())
        w._decide_approval(False)
        self.pump(1.0)
        self.assertIn("Not approved", w.chat.transcript())

    def test_screenshot(self):
        w = self.make_window()
        self.pump(8, lambda: "ONLINE" in w.conn_pill.text())
        w.input.setText("hello")
        w.send_message()
        self.pump(15, lambda: w.worker and w.worker.isFinished())
        self.pump(0.6)
        out_dir = Path(__file__).resolve().parent.parent / "docs"
        out_dir.mkdir(exist_ok=True)
        path = out_dir / "hema-ui.png"
        ok = w.grab().save(str(path))
        self.assertTrue(ok)
        self.assertTrue(path.is_file() and path.stat().st_size > 5000)


if __name__ == "__main__":
    unittest.main()
