"""Dragon Tiger historical statistics. Statistics only - no prediction of future results."""
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List

OUTCOMES = ("dragon", "tiger", "tie")

DISCLAIMER = (
    "These are historical frequencies only. Each round is independent and past results "
    "do not predict future ones. Never bet money you cannot afford to lose."
)


def wilson_interval(successes: int, n: int, z: float = 1.96):
    """95% confidence interval for a proportion (handles small samples honestly)."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


class DragonTigerStore:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS results(\n"
                "id INTEGER PRIMARY KEY AUTOINCREMENT, outcome TEXT NOT NULL,\n"
                "created REAL NOT NULL)")
            self.conn.commit()

    def add(self, outcome: str, when: float = None) -> int:
        outcome = outcome.strip().lower()
        if outcome not in OUTCOMES:
            raise ValueError(f"Outcome must be one of {OUTCOMES}")
        with self._lock:
            cur = self.conn.execute("INSERT INTO results(outcome,created) VALUES(?,?)",
                                    (outcome, when or time.time()))
            self.conn.commit()
            return cur.lastrowid

    def add_many(self, outcomes: List[str]) -> int:
        before = len(self.all())
        for o in outcomes:
            self.add(o)
        return len(self.all()) - before

    def all(self) -> List[Dict]:
        with self._lock:
            return [dict(r) for r in self.conn.execute(
                "SELECT * FROM results ORDER BY id").fetchall()]

    def delete(self, rid: int) -> bool:
        with self._lock:
            cur = self.conn.execute("DELETE FROM results WHERE id=?", (rid,))
            self.conn.commit()
            return cur.rowcount > 0

    def summary(self) -> Dict:
        rows = self.all()
        n = len(rows)
        counts = {o: 0 for o in OUTCOMES}
        for r in rows:
            counts[r["outcome"]] += 1
        stats = {}
        for o in OUTCOMES:
            lo, hi = wilson_interval(counts[o], n)
            stats[o] = {"count": counts[o],
                        "percent": round(100 * counts[o] / n, 2) if n else 0.0,
                        "ci95": [round(100 * lo, 1), round(100 * hi, 1)]}
        return {"total": n, "counts": counts, "stats": stats,
                "streaks": self._streaks(rows), "disclaimer": DISCLAIMER}

    @staticmethod
    def _streaks(rows) -> Dict:
        best = {"dragon": 0, "tiger": 0, "tie": 0}
        run_outcome, run_len = None, 0
        for r in rows:
            if r["outcome"] == run_outcome:
                run_len += 1
            else:
                run_outcome, run_len = r["outcome"], 1
            if run_outcome in best:
                best[run_outcome] = max(best[run_outcome], run_len)
        return {"longest": best}

    def report_text(self) -> str:
        s = self.summary()
        lines = [f"Dragon Tiger history ({s['total']} rounds)"]
        for o in OUTCOMES:
            st = s["stats"][o]
            lines.append(f"  {o.title():7s} {st['count']:4d}  {st['percent']:5.1f}%  95% CI {st['ci95']}")
        best = s["streaks"]["longest"]
        lines.append(f"  Longest runs: dragon {best['dragon']}, tiger {best['tiger']}, tie {best['tie']}")
        lines.append("  " + DISCLAIMER)
        return "\n".join(lines)

    def save_chart(self, path, engine=None) -> Path:
        """Bar chart of historical frequencies. Needs matplotlib (optional dependency)."""
        s = self.summary()
        labels = [o.title() for o in OUTCOMES]
        values = [s["counts"][o] for o in OUTCOMES]
        if engine is None:
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
            except ImportError as e:
                raise RuntimeError("matplotlib is not installed; run: pip install matplotlib") from e
            fig, ax = plt.subplots()
            ax.bar(labels, values)
            ax.set_title("Dragon Tiger historical frequencies")
            ax.set_ylabel("Rounds")
            fig.savefig(str(path))
            plt.close(fig)
        else:
            engine.save_bar(labels, values, str(path))
        return Path(path)

    def close(self) -> None:
        with self._lock:
            self.conn.close()
