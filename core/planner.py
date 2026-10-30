"""Breaks a request into small executable tasks using the local model."""
import json
import re
from typing import Callable, List

PLAN_PROMPT = (
    "Break the user's request into numbered, small, executable steps. "
    "Reply with ONLY a JSON array of strings. Maximum 8 steps."
)


class Plan:
    def __init__(self, steps: List[str], source: str):
        self.steps = steps
        self.source = source


def parse_plan(text: str) -> List[str]:
    match = re.search(r"\[.*\]", text, re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            steps = [str(s).strip() for s in data if str(s).strip()]
            if steps:
                return steps[:8]
        except ValueError:
            pass
    steps = [re.sub(r"^\s*(\d+[.)]|[-*])\s*", "", ln).strip()
             for ln in text.splitlines() if ln.strip()]
    return steps[:8]


class Planner:
    def __init__(self, chat: Callable[[list], str]):
        self.chat = chat

    def make_plan(self, request: str) -> Plan:
        try:
            reply = self.chat([{"role": "system", "content": PLAN_PROMPT},
                               {"role": "user", "content": request}])
            steps = parse_plan(reply)
            if steps:
                return Plan(steps, "model")
        except Exception:
            pass
        return Plan(["Handle the request directly: " + request], "fallback")
