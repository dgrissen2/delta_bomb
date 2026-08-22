"""Task-7 SPIKE (run FIRST, half-day): can the HIRO payload be polled once a
minute via CDP for a full session? Measures per-pull latency, failure rate, and
payload freshness (max utc_time vs wall clock). If this doesn't hold, STOP and
revisit the design before building anything on it (tasks.md task 7).

Run during market hours with Chrome CDP 9222 logged in to SpotGamma:
  ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_engine/spike_hiro_poll.py --minutes 90
"""
from __future__ import annotations

import argparse
import datetime as dt
import statistics
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hiro_engine.live import ET, HiroPull  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=90)
    ap.add_argument("--port", type=int, default=9222)
    args = ap.parse_args()
    day = dt.datetime.now(ET).strftime("%Y-%m-%d")
    hiro = HiroPull(port=args.port)
    lat, fails, stale = [], 0, 0
    for i in range(args.minutes):
        t0 = time.monotonic()
        try:
            frame = hiro.frame(day)
            elapsed = time.monotonic() - t0
            lat.append(elapsed)
            last_min = int(frame["min"].max())
            now_min = dt.datetime.now(ET).hour * 60 + dt.datetime.now(ET).minute
            fresh = now_min - last_min
            if fresh > 2:
                stale += 1
            print(f"[{i + 1}/{args.minutes}] ok {elapsed:.2f}s | last minute "
                  f"{last_min // 60:02d}:{last_min % 60:02d} (lag {fresh}m)")
        except Exception as e:
            fails += 1
            print(f"[{i + 1}/{args.minutes}] FAIL {time.monotonic() - t0:.2f}s: {e}")
        time.sleep(max(0.0, 60 - (time.monotonic() - t0)))
    n = len(lat)
    print("\n=== SPIKE RESULT ===")
    print(f"pulls ok {n}/{args.minutes} | failures {fails} "
          f"({fails / args.minutes:.1%}) | stale(>2m) {stale}")
    if n:
        print(f"latency p50 {statistics.median(lat):.2f}s | "
              f"max {max(lat):.2f}s | budget 5s/bar")
    ok = fails / max(args.minutes, 1) <= 0.05 and (not lat or statistics.median(lat) < 3)
    print("VERDICT:", "PASS — minutely polling holds" if ok
          else "FAIL — STOP: revisit the feed design before task 7 continues")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
