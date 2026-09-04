"""CLI (hiro_engine_v2 — the watch clone) — subcommands: backtest / scorecard ONLY.

Run: ~/Dev/virtualenvs/gamma_chaser/bin/python -m hiro_engine_v2 <cmd> --config <candidate.yaml>
The clone never runs live, never verifies the golden gate, never registers thresholds.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import REPO_ROOT, load_config
from .eventlog import EventLog
from .models import TIERS


def _log_path(cfg, name: str) -> Path:
    p = Path(cfg.get("logging", name))
    return p if p.is_absolute() else REPO_ROOT / p


def cmd_backtest(args) -> int:
    cfg = load_config(args.config)
    tier = TIERS[args.tier]
    from .backtest import available_spx_days, run_backtest
    if args.day:
        days = [args.day]
    else:
        if not (args.date_from and args.date_to):
            print("backtest needs --day or --from/--to"); return 2
        days = available_spx_days(cfg, args.date_from, args.date_to)
        if not days:
            print("no stored SPX sessions in range"); return 2
    log_path = Path(args.log) if args.log else _log_path(cfg, "paper_log").with_name(
        "paper_log_backtest.csv")
    offset = log_path.stat().st_size if log_path.exists() else 0
    log = EventLog(log_path, echo=True)         # AC: identical console stream, always
    rows = run_backtest(cfg, tier, days, log)
    log.close()
    print(f"\nbacktest done | tier={tier.tier_stamp} | {len(rows)} sessions | "
          f"CONFIG_HASH {cfg.config_hash[:12]}…")
    for r in rows:
        print(f"  {r.date}  {r.disposition}  outage={r.outage_min}m")
    # R13.3: every backtest output carries the summary contract
    import io as _io
    import pandas as pd
    from .models import EVENT_FIELDS
    from .scorecard import stage2_entries, stage3_qualify
    from .summarize import print_summary, summarize
    with open(log_path) as fh:                 # THIS run's rows only (append-only file)
        fh.seek(offset)
        tail_txt = fh.read()
    ev = pd.read_csv(_io.StringIO(",".join(EVENT_FIELDS) + "\n" + tail_txt)
                     if offset else _io.StringIO(tail_txt),
                     dtype={"session_date": str})
    print_summary(summarize(cfg, stage2_entries(ev), stage3_qualify(ev), days,
                            variant=f"backtest {days[0]}..{days[-1]} tier={tier.tier_stamp}"))
    if args.config:
        print("NOTE: --config override active — outputs stamped with that hash; "
              "never counted toward the live test.")
    return 0


def cmd_scorecard(args) -> int:
    cfg = load_config(args.config)
    from .scorecard import run_scorecard
    return run_scorecard(cfg, rehearsal=args.rehearsal,
                         d_from=args.date_from, d_to=args.date_to)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hiro_engine_v2")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def _common(p):
        p.add_argument("--config", default=None, help="config override (R8.2 hash stamped)")

    b = sub.add_parser("backtest"); _common(b)
    b.add_argument("--from", dest="date_from"); b.add_argument("--to", dest="date_to")
    b.add_argument("--day"); b.add_argument("--verbose", action="store_true")
    b.add_argument("--tier", choices=list(TIERS), default="full")
    b.add_argument("--log", default=None)
    b.set_defaults(fn=cmd_backtest)

    s = sub.add_parser("scorecard"); _common(s)
    s.add_argument("--rehearsal", action="store_true")
    s.add_argument("--from", dest="date_from"); s.add_argument("--to", dest="date_to")
    s.set_defaults(fn=cmd_scorecard)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
