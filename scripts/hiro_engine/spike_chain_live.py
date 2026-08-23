"""Task-14 LIVE QUOTE SPIKE (v3.0 hard gate — run during market hours).

Proves the SDK live option path at 1-min cadence for BOTH workloads:
  (a) full-chain snapshot at a signal minute (strike selection), and
  (b) two-strike freshness afterward (fill evaluation),
inside the 5-s post-bar budget. Writes the PASS/FAIL artifact that
`hiro_engine live` requires (docs/hiro_engine/spike_chain_live_result.json).
Neither workload passing => v3.0 CANNOT go live (no fallback exists by spec).

Run:  ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_engine/spike_chain_live.py --minutes 60
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hiro_engine.chains import LiveChains, friday_expiry_for       # noqa: E402
from hiro_engine.config import REPO_ROOT, load_config              # noqa: E402
from hiro_engine.live import ET                                    # noqa: E402

ARTIFACT = REPO_ROOT / "docs/hiro_engine/spike_chain_live_result.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=60)
    args = ap.parse_args()
    cfg = load_config()
    day = dt.datetime.now(ET).strftime("%Y-%m-%d")
    lc = LiveChains(cfg)
    print(f"spike: {day}, expiry {lc.expiry_of(day)}, {args.minutes} minutes")
    snap_lat, pair_lat, fails, stale = [], [], 0, 0
    k1 = k2 = None
    for i in range(args.minutes):
        t0 = time.monotonic()
        minute = dt.datetime.now(ET).hour * 60 + dt.datetime.now(ET).minute
        try:
            snap = lc.signal_snapshot(day, minute)                 # workload (a)
            el_a = time.monotonic() - t0
            if not len(snap):
                raise RuntimeError("empty snapshot")
            snap_lat.append(el_a)
            if k1 is None:
                from hiro_engine.instruments import InstrumentSelector
                k1, k2 = InstrumentSelector(cfg).pick_from_snapshot(snap, "sell_first")
                print(f"  strikes selected: {k1}/{k2}")
            t1 = time.monotonic()
            qv = lc.quote_view(day, minute, k1, k2)                # workload (b)
            el_b = time.monotonic() - t1
            pair_lat.append(el_b)
            ok2 = qv.leg1 is not None and qv.leg2 is not None and qv.leg1.valid and qv.leg2.valid
            if not ok2:
                stale += 1
            print(f"[{i+1}/{args.minutes}] snap {el_a:.2f}s ({len(snap)} rows) | "
                  f"pair {el_b:.2f}s | quotes {'OK' if ok2 else 'INVALID'}")
        except Exception as e:
            fails += 1
            print(f"[{i+1}/{args.minutes}] FAIL: {e}")
        time.sleep(max(0.0, 60 - (time.monotonic() - t0)))
    n = args.minutes
    ok = (fails / n <= 0.05 and stale / n <= 0.05
          and snap_lat and statistics.median(snap_lat) < 3.0
          and pair_lat and statistics.median(pair_lat) < 2.0)
    result = dict(verdict="PASS" if ok else "FAIL", day=day, minutes=n,
                  failures=fails, stale=stale,
                  snap_p50=round(statistics.median(snap_lat), 3) if snap_lat else None,
                  pair_p50=round(statistics.median(pair_lat), 3) if pair_lat else None,
                  criteria="fail<=5%, stale<=5%, snap p50<3s, pair p50<2s (5-s budget)")
    ARTIFACT.write_text(json.dumps(result, indent=1))
    print(f"\n=== SPIKE {result['verdict']} === -> {ARTIFACT}")
    if not ok:
        print("STOP: v3.0 cannot go live — revisit the live-quote design (Schwab fallback?)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
