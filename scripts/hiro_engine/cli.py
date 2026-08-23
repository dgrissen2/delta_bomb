"""CLI — subcommands: backtest / verify / live / scorecard / sweep.

Run: ~/Dev/virtualenvs/gamma_chaser/bin/python -m hiro_engine <cmd> ...
(from the repo's scripts/ directory on PYTHONPATH, or via scripts/hiro_engine).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .config import REPO_ROOT, load_config
from .eventlog import EventLog
from .models import TIERS


def _log_path(cfg, name: str) -> Path:
    p = Path(cfg.get("logging", name))
    return p if p.is_absolute() else REPO_ROOT / p


def _hash_warning(cfg) -> None:
    """R8.2: loud reset warning when CONFIG_HASH differs from the prior session."""
    p = _log_path(cfg, "sessions_log")
    if not p.exists():
        return
    last = None
    with open(p, newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("mode") in ("live", "shakedown"):
                last = row
    if last and last.get("config_hash") and last["config_hash"] != cfg.config_hash:
        print("\n" + "!" * 78)
        print("!! CONFIG_HASH CHANGED vs the previous session.")
        print(f"!! previous: {last['config_hash'][:16]}…   current: {cfg.config_hash[:16]}…")
        print("!! Mixing hashes RESETS the 10-session acceptance test (R9).")
        print("!" * 78 + "\n")


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


def cmd_verify(args) -> int:
    cfg = load_config(args.config)
    from .verify import run_verification
    r = run_verification(cfg)
    print(f"verification vs {cfg.verification_artifact.name}: "
          f"{'PASS' if r.ok else 'FAIL'} ({r.n_engine}/{r.n_artifact} trades; "
          f"artifact hash {'ok' if r.artifact_hash_ok else 'MISMATCH'})")
    for m in r.mismatches:
        print("  DEFECT:", m)
    return 0 if r.ok else 1


def cmd_live(args) -> int:
    cfg = load_config(args.config)
    _hash_warning(cfg)
    from .live import run_live
    return run_live(cfg, shakedown=args.shakedown)


def cmd_scorecard(args) -> int:
    cfg = load_config(args.config)
    from .scorecard import run_scorecard
    return run_scorecard(cfg, rehearsal=args.rehearsal,
                         d_from=args.date_from, d_to=args.date_to)


def cmd_sweep(args) -> int:
    cfg = load_config(args.config)
    from .sweep import run_sweep
    return run_sweep(cfg, args.knob, d_from=args.date_from, d_to=args.date_to)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hiro_engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def _common(p):
        p.add_argument("--config", default=None, help="config override (R8.2 hash stamped)")

    b = sub.add_parser("backtest"); _common(b)
    b.add_argument("--from", dest="date_from"); b.add_argument("--to", dest="date_to")
    b.add_argument("--day"); b.add_argument("--verbose", action="store_true")
    b.add_argument("--tier", choices=list(TIERS), default="full")
    b.add_argument("--log", default=None)
    b.set_defaults(fn=cmd_backtest)

    v = sub.add_parser("verify"); _common(v); v.set_defaults(fn=cmd_verify)

    l = sub.add_parser("live"); _common(l)
    l.add_argument("--shakedown", action="store_true"); l.set_defaults(fn=cmd_live)

    s = sub.add_parser("scorecard"); _common(s)
    s.add_argument("--rehearsal", action="store_true")
    s.add_argument("--from", dest="date_from"); s.add_argument("--to", dest="date_to")
    s.set_defaults(fn=cmd_scorecard)

    pc = sub.add_parser("parity-check"); _common(pc)
    pc.add_argument("day")
    pc.set_defaults(fn=lambda a: __import__("hiro_engine.parity", fromlist=["run_parity_cli"])
                    .run_parity_cli(load_config(a.config), a.day))

    rg = sub.add_parser("register-thresholds"); _common(rg)
    rg.add_argument("--log", default=None)
    rg.set_defaults(fn=lambda a: __import__("hiro_engine.register", fromlist=["run_register"])
                    .run_register(load_config(a.config),
                                  log_path=Path(a.log) if a.log else None))

    w = sub.add_parser("sweep"); _common(w)
    w.add_argument("knob")
    w.add_argument("--from", dest="date_from"); w.add_argument("--to", dest="date_to")
    w.set_defaults(fn=cmd_sweep)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
