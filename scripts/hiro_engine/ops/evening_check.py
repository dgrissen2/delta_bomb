"""Evening ops (task 11): verify today's captures and logs.

  ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_engine/ops/evening_check.py [--day D]

Checks: today's HIRO partition exists + manifest sha256 matches the file bytes;
paper_log has today's disposition row (flags partial); SPX parquet stored;
SPY store staleness (known gap, warn only).
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hiro_engine.config import REPO_ROOT, load_config    # noqa: E402

ET = ZoneInfo("America/New_York")
G, R, Y = "\033[32mOK\033[0m", "\033[31mRED\033[0m", "\033[33mWARN\033[0m"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=dt.datetime.now(ET).strftime("%Y-%m-%d"))
    day = ap.parse_args().day
    cfg = load_config()
    red = 0

    def line(ok, label, detail, warn_only=False):
        nonlocal red
        tag = G if ok else (Y if warn_only else R)
        if not ok and not warn_only:
            red += 1
        print(f"  [{tag}] {label}: {detail}")

    print(f"=== hiro_engine evening check — {day} ===")
    root = cfg.path_of("hiro_root")
    part = Path(root) / f"date={day}"
    norm = part / "normalized" / "hiro_series.csv"
    line(norm.exists(), "HIRO partition", str(norm) if norm.exists()
         else f"MISSING — run the backfill before the vendor window closes")
    manifest_p = Path(root) / "manifest.json"
    if not manifest_p.exists():
        line(False, "manifest", f"{manifest_p} MISSING — store integrity unverifiable")
    if norm.exists() and manifest_p.exists():
        m = json.load(open(manifest_p))
        sess = (m.get("sessions") or {}).get(day)
        if not sess:
            line(False, "manifest", f"no entry for {day}")
        else:
            ok_n = hashlib.sha256(norm.read_bytes()).hexdigest() == sess.get("normalized_sha256")
            line(ok_n, "manifest normalized sha256", "matches" if ok_n else "MISMATCH")
            raw_p = Path(root) / sess.get("raw_path", "")
            if raw_p.exists() and sess.get("raw_uncompressed_sha256"):
                raw_ok = hashlib.sha256(gzip.open(raw_p, "rb").read()).hexdigest() \
                    == sess["raw_uncompressed_sha256"]
                line(raw_ok, "manifest raw sha256", "matches" if raw_ok else "MISMATCH")
            line(sess.get("status") == "available", "capture status",
                 str(sess.get("status")), warn_only=True)
    spx = cfg.path_of("spx_dir") / f"{day}.parquet"
    line(spx.exists(), "SPX 1-min parquet", str(spx.name) if spx.exists() else "MISSING")
    if spx.exists():
        import pandas as pd
        last_bar = int(pd.read_parquet(spx)["min"].max())
        frozen = day in cfg.control_days
        line(last_bar >= 955 or frozen, "SPX capture completeness",
             f"ends {last_bar // 60:02d}:{last_bar % 60:02d}"
             + (" (frozen control day — hash-pinned, DO NOT refresh)" if frozen and last_bar < 955
                else "" if last_bar >= 955 else " -> INCOMPLETE, refresh from ThetaData"),
             warn_only=frozen)
    log_p = Path(cfg.get("logging", "paper_log"))
    log_p = log_p if log_p.is_absolute() else REPO_ROOT / log_p
    if log_p.exists():
        import csv as _csv
        dispo = None
        with open(log_p, newline="") as fh:
            for row in _csv.DictReader(fh):
                if row.get("session_date") == day and row.get("event_type") == "disposition":
                    dispo = row.get("notes")
        line(dispo is not None, "paper_log disposition",
             dispo or "no disposition row for today (session did not finish?)",
             warn_only=True)
        if dispo and "partial" in dispo:
            line(False, "session disposition", f"PARTIAL — excluded from the R9 test: {dispo}",
                 warn_only=True)
    else:
        line(False, "paper_log", "no log file yet", warn_only=True)
    sc = Path(f"docs/replay/hiro/live_quotes_{day}.parquet")
    line(sc.exists(), "snapshot sidecar (live parity/resume)",
         str(sc.name) if sc.exists() else "missing (fine if today was not a live session)",
         warn_only=True)
    import pandas as pd
    spy = pd.read_parquet(cfg.path_of("spy_parquet"), columns=["date"])
    line(str(spy.date.max()) >= day, "SPY 1-min store",
         f"latest {spy.date.max()} (stale is a known gap — live uses ThetaData; "
         "backfill when convenient)", warn_only=True)
    print("\nALL GREEN" if red == 0 else f"\n{red} RED check(s)")
    return 0 if red == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
