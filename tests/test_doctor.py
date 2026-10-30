import tempfile
import unittest
from pathlib import Path

from config import Config
from core.doctor import format_report, run_checks
from tests.fake_ollama import start_server


def make_config(host, model="llama:latest"):
    root = Path(tempfile.mkdtemp())
    return Config(host, model, 5.0, 20, "sys", workspace_dir=root / "ws",
                  data_dir=root / "data", logs_dir=root / "logs", backups_dir=root / "bk")


class DoctorTests(unittest.TestCase):
    def test_all_good_with_server(self):
        server, url, _ = start_server(("llama:latest",))
        self.addCleanup(server.shutdown)
        checks = run_checks(make_config(url))
        by_name = {c[0]: c for c in checks}
        self.assertTrue(by_name["Ollama port"][1])
        self.assertTrue(by_name["Ollama API"][1])
        self.assertTrue(by_name["Ollama models"][1])
        self.assertTrue(by_name["Preferred model"][1])
        self.assertTrue(by_name["Folder workspace"][1])
        self.assertIn("All critical checks passed", format_report(checks))

    def test_connection_refused_and_missing_model(self):
        checks = {c[0]: c for c in run_checks(make_config("http://127.0.0.1:1"))}
        self.assertFalse(checks["Ollama port"][1])
        self.assertIn("problem(s) found", format_report(list(checks.values())))
        server, url, _ = start_server(("other:1",))
        self.addCleanup(server.shutdown)
        checks2 = {c[0]: c for c in run_checks(make_config(url))}
        self.assertFalse(checks2["Preferred model"][1])
        self.assertIn("other:1", checks2["Preferred model"][2])

    def test_optional_marker_is_none_or_bool(self):
        server, url, _ = start_server(("llama:latest",))
        self.addCleanup(server.shutdown)
        for name, ok, _ in run_checks(make_config(url)):
            if name.startswith("Optional"):
                self.assertIn(ok, (True, None))


if __name__ == "__main__":
    unittest.main()
