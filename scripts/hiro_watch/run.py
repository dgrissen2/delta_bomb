"""hiro_watch W3 — the evening command.

    python hiro_watch/run.py <date>              backtest <date> through every candidate yaml
    python hiro_watch/run.py --rebuild NAME|all  delete a candidate's logs and backtest every baseline session

Every candidate is a yaml in docs/hiro_watch/configs/ (registry.py validates them). Its
`watch.engine` names the package (hiro_engine = frozen v1, hiro_engine_v2 = the knob clone); its
`logging` paths give it its own log dir. No silent skips (W0.3): any refusal or non-zero engine
exit stops the run with the reason.
"""
from __future__ import annotations

import argparse
import csv
import logging
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hiro_watch.registry import (BASELINE_DIR, SCRIPTS, WATCH_ROOT, Candidate, baseline_data,  # noqa: E402
                                 candidates)

BASELINE_SESSIONS = BASELINE_DIR / "sessions_backtest.csv"
log = logging.getLogger("hiro_watch.run")


def _column(path: Path, col: str) -> list[str]:
    if not path.exists():
        return []
    with open(path, newline="") as fh:
        return [r[col] for r in csv.DictReader(fh)]


def baseline_sessions() -> list[str]:
    era = str(baseline_data()["hiro_era_start"])
    days = sorted(d for d in _column(BASELINE_SESSIONS, "date") if d >= era)
    if not days:
        raise SystemExit(f"REFUSED: no baseline sessions >= {era} in {BASELINE_SESSIONS}")
    return days


def logged(c: Candidate) -> set[str]:
    """Dates present in the candidate's sessions file OR its paper log (an aborted run leaves a banner)."""
    return set(_column(c.sessions, "date")) | set(_column(c.paper_log, "session_date"))


def _backtest(c: Candidate, *args: str) -> None:
    cmd = [sys.executable, "-m", c.engine, "backtest", "--config", str(c.path), *args]
    log.debug("exec %s", " ".join(cmd))
    print(f"\n=== {c.name} ({c.engine}) {' '.join(args)} ===")
    r = subprocess.run(cmd, cwd=SCRIPTS)
    if r.returncode != 0:
        raise SystemExit(f"REFUSED: {c.name} backtest exited {r.returncode} — nothing after it ran")


def run_day(day: str) -> None:
    cands = candidates()
    if day not in set(baseline_sessions()):
        raise SystemExit(f"REFUSED: baseline has no session row for {day} in {BASELINE_SESSIONS} "
                         "— run the v1 backtest for that day first")
    dup = [c.name for c in cands if day in logged(c)]
    if dup:
        raise SystemExit(f"REFUSED: {day} already logged for {dup} (W0.3: no duplicate sessions; "
                         "use --rebuild to regenerate)")
    for c in cands:
        _backtest(c, "--day", day)
    print(f"\nhiro_watch: {day} appended to {len(cands)} candidates")


def rebuild(name: str) -> None:
    cands = [c for c in candidates() if name in ("all", c.name)]
    if not cands:
        raise SystemExit(f"REFUSED: no candidate named {name!r}")
    days = baseline_sessions()
    for c in cands:
        if c.log_dir.exists():
            if c.log_dir.parent != WATCH_ROOT or c.log_dir.name != c.name:     # registry guarantees this
                raise SystemExit(f"REFUSED: will not delete {c.log_dir}")
            shutil.rmtree(c.log_dir)
        _backtest(c, "--from", days[0], "--to", days[-1])
        extra = logged(c) - set(days)
        if extra:
            raise SystemExit(f"REFUSED: {c.name} logged sessions the baseline lacks: {sorted(extra)}")
    print(f"\nhiro_watch: rebuilt {[c.name for c in cands]} over {days[0]}..{days[-1]} ({len(days)} sessions)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hiro_watch/run.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("day", nargs="?", help="session date YYYY-MM-DD")
    ap.add_argument("--rebuild", metavar="NAME|all")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.debug else logging.INFO, format="%(message)s")
    if a.debug:
        print("[debug on]")
    if bool(a.day) == bool(a.rebuild):
        ap.error("give exactly one of <date> or --rebuild")
    if a.rebuild:
        rebuild(a.rebuild)
    else:
        run_day(a.day)
    return 0


if __name__ == "__main__":
    sys.exit(main())
