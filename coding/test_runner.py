"""Runs the project's Python tests via the approved command runner."""
import re
from typing import Tuple


class TestRunner:
    def __init__(self, runner, python_path: str = None):
        self.runner = runner
        self.python = python_path or "python3"

    def run_unittest(self, subdir: str = ".") -> Tuple[bool, str]:
        cmd = f'cd "{subdir}" && "{self.python}" -W ignore -m unittest discover -s . -t . -p "test_*.py" 2>&1'
        if subdir == ".":
            cmd = f'"{self.python}" -W ignore -m unittest discover -s . -t . -p "test_*.py" 2>&1'
        code, out = self.runner.run(cmd)
        return code == 0, out


def summarize_test_output(output: str) -> str:
    ok = re.search(r"Ran (\d+) tests?", output)
    failed = "FAILED" in output
    if ok:
        return f"Ran {ok.group(1)} tests; {'FAILED' if failed else 'OK'}"
    return "Could not parse test output"
