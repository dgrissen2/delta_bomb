"""Per-session v1 vs one candidate, realized cash, with the event tag — the owner's daily table.

    python hiro_watch/daily_table.py [a2_size1_c30]
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hiro_watch import compare as C                      # noqa: E402
from hiro_watch.events import tag                        # noqa: E402
from hiro_watch.regime import tag as regime_tag           # noqa: E402
from hiro_watch.registry import baseline_data, candidates  # noqa: E402


def _cell(x: pd.DataFrame) -> str:
    return "—" if not len(x) else f"{len(x)}/{int(x.bomb.sum())} {x.pnl_usd.sum():+.0f}"


def table(name: str) -> str:
    cand = next(c for c in candidates() if c.name == name)
    era = str(baseline_data()["hiro_era_start"])
    bt = C.trades(C.load_log(C.V1_LOGS))
    ct = C.trades(C.load_log([cand.paper_log], expect_hash=cand.config_hash))
    bt, ct = bt[bt.session_date >= era], ct[ct.session_date >= era]
    sess = C.load_sessions(C.V1_SESSIONS); sess = sess[sess.date >= era].sort_values("date")
    out = [f"| date | event | regime | disp | v1 A t/b $ | v1 B t/b $ | **v1 day** | {name} A | {name} B | **{name} day** | diff |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for d, disp in zip(sess.date, sess.disposition):
        b, c = bt[bt.session_date == d], ct[ct.session_date == d]
        p1, p2 = b.pnl_usd.sum(), c.pnl_usd.sum()
        out.append(f"| {d} | {tag(d) or ''} | {regime_tag(d) or ''} | {disp} | {_cell(b[b.branch == 'A'])} | {_cell(b[b.branch == 'B'])} | {p1:+.0f} | "
                   f"{_cell(c[c.branch == 'A'])} | {_cell(c[c.branch == 'B'])} | {p2:+.0f} | {p2 - p1:+.0f} |")
    p1, p2 = bt.pnl_usd.sum(), ct.pnl_usd.sum()
    out.append(f"| **TOTAL** | | | {len(sess)} | {_cell(bt[bt.branch == 'A'])} | {_cell(bt[bt.branch == 'B'])} | **{p1:+.0f}** | "
               f"{_cell(ct[ct.branch == 'A'])} | {_cell(ct[ct.branch == 'B'])} | **{p2:+.0f}** | **{p2 - p1:+.0f}** |")
    ev = sess.date.map(tag) != ""
    for label, m in (("event days", ev), ("plain days", ~ev)):
        days = set(sess.date[m])
        b, c = bt[bt.session_date.isin(days)], ct[ct.session_date.isin(days)]
        out.append(f"| *{label}* | | | {len(days)} | {_cell(b[b.branch == 'A'])} | {_cell(b[b.branch == 'B'])} | {b.pnl_usd.sum():+.0f} | "
                   f"{_cell(c[c.branch == 'A'])} | {_cell(c[c.branch == 'B'])} | {c.pnl_usd.sum():+.0f} | {c.pnl_usd.sum() - b.pnl_usd.sum():+.0f} |")
    out.append(f"\nworst trade: v1 {bt.pnl_usd.min():+.0f} | {name} {ct.pnl_usd.min():+.0f}; "
               f"bombs v1 {int(bt.bomb.sum())} | {name} {int(ct.bomb.sum())}")
    return "\n".join(out)


if __name__ == "__main__":
    print(table(sys.argv[1] if len(sys.argv) > 1 else "a2_size1_c30"))
