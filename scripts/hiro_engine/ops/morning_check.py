"""Morning ops (task 11): ONE command, green/red output. Run before `live`.

Data source: ThetaData Python SDK (creds-file auth, no terminal).

  ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_engine/ops/morning_check.py

Checks: HIRO store freshness (vendor retains ~5 sessions — a missed day is
unrecoverable), SPX 1-min freshness, levels CSV row for today, event calendar,
ThetaData terminal, Chrome CDP + SpotGamma login.
"""
from __future__ import annotations

import datetime as dt
import socket
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hiro_engine.calendar import CalendarLoader          # noqa: E402
from hiro_engine.config import load_config               # noqa: E402
from hiro_engine.levels import LevelsLoader              # noqa: E402

ET = ZoneInfo("America/New_York")
G, R, Y = "\033[32mOK\033[0m", "\033[31mRED\033[0m", "\033[33mWARN\033[0m"


def prev_trading_day(d: dt.date) -> dt.date:
    d -= dt.timedelta(days=1)
    while d.weekday() > 4:
        d -= dt.timedelta(days=1)
    return d


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    cfg = load_config()
    today = dt.datetime.now(ET).date()
    prev = prev_trading_day(today)
    prev2 = prev_trading_day(prev)          # holiday fallback (finding 6)
    red = 0

    def line(ok, label, detail, warn_only=False):
        nonlocal red
        tag = G if ok else (Y if warn_only else R)
        if not ok and not warn_only:
            red += 1
        print(f"  [{tag}] {label}: {detail}")

    print(f"=== hiro_engine morning check — {today} ===")
    hiro_root = cfg.path_of("hiro_root")
    latest_hiro = sorted(p.name[5:] for p in Path(hiro_root).glob("date=*")
                         if (p / "normalized" / "hiro_series.csv").exists())   # (7) empty partition != captured
    line(bool(latest_hiro) and latest_hiro[-1] >= str(prev2), "HIRO store",
         f"latest COMPLETE partition {latest_hiro[-1] if latest_hiro else 'NONE'} "
         f"(need >= {prev2}; {prev} expected unless it was a holiday; "
         f"vendor keeps ~5 sessions — run the backfill NOW if red)")
    spx_dir = cfg.path_of("spx_dir")
    latest_spx = sorted(p.stem for p in Path(spx_dir).glob("????-??-??.parquet"))
    line(bool(latest_spx) and latest_spx[-1] >= str(prev2), "SPX 1-min store",
         f"latest {latest_spx[-1] if latest_spx else 'NONE'} (need >= {prev2}; "
         f"{prev} expected unless holiday)")
    if latest_spx:
        import pandas as pd
        last_bar = int(pd.read_parquet(Path(spx_dir) / f"{latest_spx[-1]}.parquet")["min"].max())
        frozen = latest_spx[-1] in cfg.control_days
        line(last_bar >= 955 or frozen, "SPX capture completeness",
             f"{latest_spx[-1]} ends {last_bar // 60:02d}:{last_bar % 60:02d}"
             + (" (frozen control day — hash-pinned, DO NOT refresh)" if frozen and last_bar < 955
                else "" if last_bar >= 955 else
                " -> INCOMPLETE, refresh from ThetaData (feeds the live range60 pool!)"),
             warn_only=frozen)
    lv = LevelsLoader(cfg.path_of("levels_csv")).load(str(today))
    line(lv.valid, "SG levels", f"row for {today}: "
         + (f"VT={lv.vt} CW={lv.cw}" if lv.valid
            else "MISSING/INVALID -> engine enforces LONG-FIRST ONLY (R4.2)"),
         warn_only=True)
    cal = CalendarLoader(cfg.path_of("calendar_csv"))
    ev = cal.check(str(today))
    line(not ev.is_event_day, "event calendar",
         f"{today} {'EVENT DAY: ' + ev.reason + ' -> STAND DOWN (R4.4)' if ev.is_event_day else 'clear'}",
         warn_only=True)
    month_rows = [d for d in cal.manual if d[:7] == str(today)[:7]]
    line(bool(month_rows), "CPI/FOMC entries",
         f"{len(month_rows)} manual rows for {str(today)[:7]} "
         "(empty -> add release dates to docs/hiro_engine/event_calendar.csv)",
         warn_only=True)
    try:
        from hiro_engine.live import spx_bars_today
        try:
            n = len(spx_bars_today(str(prev)))
            ref = prev
        except Exception:
            n = len(spx_bars_today(str(prev2)))   # holiday fallback
            ref = prev2
        line(n > 150, "ThetaData SDK",
             f"{n} SPX bars for {ref} (creds-file auth, no terminal"
             + ("; half-day?" if n <= 300 else "") + ")")
    except Exception as e:
        line(False, "ThetaData SDK", f"pull failed: {e}")
    cdp = port_open(9222)
    line(cdp, "Chrome CDP", "port 9222 (--remote-debugging-port=9222)")
    if cdp:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                b = pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
                page = b.contexts[0].new_page()
                page.goto("https://dashboard.spotgamma.com/hiro", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=30000)
                ok = bool(page.evaluate("() => !!window.localStorage.getItem('sgToken')"))
                page.close()
            line(ok, "SpotGamma login", "sgToken present" if ok
                 else "NOT LOGGED IN -> log in at dashboard.spotgamma.com")
        except Exception as e:
            line(False, "SpotGamma login", f"check failed: {e}")
    print(("\nALL GREEN — start the engine: python -m hiro_engine live"
           if red == 0 else f"\n{red} RED check(s) — fix before starting"))
    return 0 if red == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
