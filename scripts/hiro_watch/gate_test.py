"""Does an entry gate SELECT, or does it only reduce exposure? (W6.6 diagnostic, 2026-09-12)

A gate that keeps N of M trades improves a losing book by arithmetic alone. This asks whether the
kept trades are better than an arbitrary N-of-M cut: it compares the gated subset's cash and
completion rate against the distribution of random same-size subsets of the SAME trades.

    python hiro_watch/gate_test.py [--branch A] [--field r30] [--lt -2.0] [--candidate a2_size1_c30]

Reporting only — never a bar. Baseline (v1) trades joined to the FIRST signal of each setup, which is
where the engine's own gate reads its flow number.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hiro_watch import compare as C                        # noqa: E402
from hiro_watch.registry import baseline_data, candidates  # noqa: E402

DRAWS = 20000
SEED = 7


def gated_vs_random(branch: str, field: str, lt: float, draws: int = DRAWS) -> dict:
    era = str(baseline_data()["hiro_era_start"])
    ev = C.load_log(C.V1_LOGS)
    ev = ev[ev.session_date >= era]
    t, sig = C.trades(ev), C.signals(ev)
    first = sig.sort_values("signal_min").drop_duplicates(C.SETUP, keep="first")[C.SETUP + [field]]
    a = t[t.branch == branch].merge(first, on=C.SETUP, how="left").dropna(subset=[field])
    keep, block = a[a[field] < lt], a[a[field] >= lt]
    rng = np.random.default_rng(SEED)
    d = np.array([a.pnl_usd.sample(len(keep), random_state=int(s)).sum()
                  for s in rng.integers(0, 10**6, draws)])
    r = np.array([a.bomb.sample(len(keep), random_state=int(s)).mean()
                  for s in rng.integers(0, 10**6, draws // 4)])
    return dict(all=a, keep=keep, block=block, draws=d,
                cash_pct=float((d < keep.pnl_usd.sum()).mean() * 100),
                rate_pct=float((r < keep.bomb.mean()).mean() * 100), rate_mean=float(r.mean()))


def decompose(name: str, branch: str) -> pd.DataFrame:
    """Candidate trades split into those the baseline also took and those only the candidate reached
    (capacity the gate freed — the engine allows one unpaired leg at a time)."""
    era = str(baseline_data()["hiro_era_start"])
    bt = C.trades(C.load_log(C.V1_LOGS))
    bt = bt[(bt.session_date >= era) & (bt.branch == branch)]
    c = next(x for x in candidates() if x.name == name)
    ct = C.trades(C.load_log([c.paper_log], expect_hash=c.config_hash))
    ct = ct[ct.branch == branch]
    kv = set(map(tuple, bt[["session_date", "entry_min"]].values))
    ct = ct.assign(shared=[tuple(x) in kv for x in ct[["session_date", "entry_min"]].values])
    shared = ct[ct.shared]
    base_shared = bt.merge(shared[["session_date", "entry_min"]], on=["session_date", "entry_min"])
    return pd.DataFrame([
        dict(source="baseline trades the gate BLOCKED", n=len(bt) - len(shared),
             cash=bt.pnl_usd.sum() - base_shared.pnl_usd.sum()),
        dict(source="shared trades — credit effect", n=len(shared),
             cash=shared.pnl_usd.sum() - base_shared.pnl_usd.sum()),
        dict(source="candidate-only trades (freed capacity)", n=int((~ct.shared).sum()),
             cash=ct[~ct.shared].pnl_usd.sum()),
    ])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch", default="A")
    ap.add_argument("--field", default="r30")
    ap.add_argument("--lt", type=float, default=-2.0)
    ap.add_argument("--candidate", default="a2_size1_c30")
    a = ap.parse_args(argv)
    g = gated_vs_random(a.branch, a.field, a.lt)
    k, b, d = g["keep"], g["block"], g["draws"]
    print(f"Branch {a.branch}: {len(g['all'])} baseline trades with {a.field}; gate = {a.field} < {a.lt}")
    for lab, x in ((f"  kept   ({a.field} < {a.lt})", k), (f"  blocked({a.field} >= {a.lt})", b)):
        print(f"{lab}  n={len(x):3}  bombs {int(x.bomb.sum()):3} ({x.bomb.mean():.2f})  "
              f"cash {x.pnl_usd.sum():+7.0f}  per trade {x.pnl_usd.mean():+7.1f}")
    print(f"\n  random {len(k)}-of-{len(g['all'])} subsets: mean cash {d.mean():+.0f} "
          f"[p5 {np.percentile(d, 5):+.0f}, p95 {np.percentile(d, 95):+.0f}]")
    print(f"  gate cash {k.pnl_usd.sum():+.0f} -> {g['cash_pct']:.0f}th percentile of chance")
    print(f"  gate completion {k.bomb.mean():.2f} vs random {g['rate_mean']:.2f} -> {g['rate_pct']:.0f}th percentile")
    print(f"\n{a.candidate} Branch {a.branch} — where its edge comes from:")
    print(decompose(a.candidate, a.branch).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
