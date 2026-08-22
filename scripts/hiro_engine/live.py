"""Live plumbing (task 7): ThetaData SPX/SPY bars, HIRO snapshot via the
logged-in Chrome CDP session (IMPORTED from HIRO_finder — not copied, DRY
ledger), optional Schwab chain adapter, and the live session loop.

Requires: ThetaData terminal up (localhost:25510); Chrome with
--remote-debugging-port=9222 logged in to dashboard.spotgamma.com.
Run via: python -m hiro_engine live [--shakedown]
"""
from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from .config import REPO_ROOT, Config
from .eventlog import EventLog
from .feeds import ReplayTick, hiro_minute_frame
from .models import Bar, Event, SpyBar, TIER_FULL
from .session import Session, build_range60_history

ET = ZoneInfo("America/New_York")
THETA = "http://127.0.0.1:25510"
HIRO_FINDER = Path("~/Dev/HIRO_finder").expanduser()
SYMBOL = "S&P 500"
CDP_PORT = 9222


# ---------------------------------------------------------------------------
# ThetaData (R2.1 / R2.6): re-request today's history each minute — simple,
# stateless, and self-healing after a stall.
# ---------------------------------------------------------------------------
def _theta_bars(url: str, params: dict) -> pd.DataFrame:
    r = requests.get(url, params=params, timeout=4)
    r.raise_for_status()
    j = r.json()
    cols = [c.lower() for c in j["header"]["format"]]
    return pd.DataFrame(j["response"], columns=cols)


def spx_bars_today(day: str) -> pd.DataFrame:
    """Completed SPX 1-min bars for `day`, columns min/open/high/low/close."""
    ymd = day.replace("-", "")
    df = _theta_bars(f"{THETA}/v2/hist/index/price", dict(
        root="SPX", start_date=ymd, end_date=ymd, ivl=60000)) \
        if False else _theta_bars(f"{THETA}/v2/hist/index/ohlc", dict(
            root="SPX", start_date=ymd, end_date=ymd, ivl=60000))
    df["min"] = (df.ms_of_day // 60000).astype(int)
    return df[["min", "open", "high", "low", "close"]]


def spy_bars_today(day: str) -> pd.DataFrame:
    ymd = day.replace("-", "")
    df = _theta_bars(f"{THETA}/v2/hist/stock/ohlc", dict(
        root="SPY", start_date=ymd, end_date=ymd, ivl=60000))
    df["min"] = (df.ms_of_day // 60000).astype(int)
    return df[["min", "open", "high", "low", "close", "volume"]]


# ---------------------------------------------------------------------------
# HIRO via CDP (R2.2) — session code imported from HIRO_finder
# ---------------------------------------------------------------------------
class HiroPull:
    def __init__(self, port: int = CDP_PORT):
        sys.path.insert(0, str(HIRO_FINDER))
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        browser = self._pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        pages = [p for c in browser.contexts for p in c.pages
                 if "spotgamma.com" in (p.url or "")]
        if pages:
            self.page = pages[0]
        else:
            # open our own tab in the logged-in profile (sgToken is origin-scoped)
            if not browser.contexts:
                raise RuntimeError("CDP browser has no contexts")
            self.page = browser.contexts[0].new_page()
            self.page.goto("https://dashboard.spotgamma.com/hiro", timeout=30000)
            self.page.wait_for_timeout(2000)
            if not self.page.evaluate("() => !!window.localStorage.getItem('sgToken')"):
                raise RuntimeError("SpotGamma not logged in in the CDP browser — "
                                   "log in at dashboard.spotgamma.com and retry")

    def frame(self, day: str) -> pd.DataFrame:
        """Fresh full-day minute frame (the payload is cumulative; we rebuild
        the frame each pull — same transform as the stored partitions)."""
        from hiro_tickers.historical_backfill import fetch_historical_hiro_payload
        from hiro_tickers.live_monitor import (normalized_series_rows,
                                               symbol_payload_for_ticker)
        payload = fetch_historical_hiro_payload(
            self.page, symbol=SYMBOL, start_date=day, end_date=day, timeout_ms=8000)
        sym = symbol_payload_for_ticker(payload, SYMBOL)
        rows = []
        for group in ("all", "nextExp"):
            raw = sym.get(group) or []
            rows.extend(normalized_series_rows(raw, group))
        if not rows:
            raise RuntimeError("HIRO payload contained no series rows")
        return hiro_minute_frame(pd.DataFrame(rows))


# ---------------------------------------------------------------------------
# Schwab chain adapter (R2.5) — optional; engine runs proxy-mode without it
# ---------------------------------------------------------------------------
class ChainAdapter:
    """Wire to the user's Schwab tooling when available. Until wired+validated
    in a live session, chain_available stays False and every signal uses the
    R1.2 'nearest -0.20Δ' hint with spot-proxy caps/resolutions (R2.5)."""
    available = False

    def option_mid_move(self, trade) -> Optional[float]:
        return None

    def implied_debit(self, trade) -> Optional[float]:
        return None

    def atm_straddle_im(self, day: str) -> Optional[float]:
        return None


# ---------------------------------------------------------------------------
def run_live(cfg: Config, shakedown: bool = False) -> int:
    day = dt.datetime.now(ET).strftime("%Y-%m-%d")
    log_p = Path(cfg.get("logging", "paper_log"))
    if not log_p.is_absolute():
        log_p = REPO_ROOT / log_p
    log = EventLog(log_p)
    chain = ChainAdapter()
    im = chain.atm_straddle_im(day) if chain.available else None
    era = str(cfg.get("data", "hiro_era_start"))
    from .backtest import available_spx_days
    hist_days = [d for d in available_spx_days(cfg, era, day) if d < day]
    hist = build_range60_history(cfg, TIER_FULL, hist_days)
    session = Session(cfg, TIER_FULL, day, "live", log, range60_history=hist,
                      shakedown=shakedown, chain_available=chain.available, im=im)
    hiro = HiroPull()

    # crash-resume: rows for today already logged -> warm replay (muted)
    resume_rows = False
    if log_p.exists():
        try:
            prior = pd.read_csv(log_p, dtype={"session_date": str})
            resume_rows = bool((prior.session_date == day).any())
        except Exception:
            resume_rows = False
    processed_min = 569
    if resume_rows:
        print(f"[resume] found today's rows in {log_p.name} — warm replaying…")
        spx = spx_bars_today(day)
        spy = spy_bars_today(day)
        hframe = hiro.frame(day)
        spy_map = {int(r.min): SpyBar(int(r.min), r.open, r.high, r.low, r.close, r.volume)
                   for r in spy.itertuples()}
        ticks = []
        for r in spx.itertuples():
            m = int(r.min)
            if 570 <= m <= 960:
                ticks.append(ReplayTick(Bar(m, r.open, r.high, r.low, r.close),
                                        spy_map.get(m), hframe[hframe["min"] <= m]))
        session.warm_replay(ticks)
        processed_min = session.last_bar_min or 569
        print(f"[resume] warm state rebuilt through {processed_min // 60:02d}:{processed_min % 60:02d}")
    else:
        log.emit(session._stamp(session.startup_events(), None))
        if session.calendar.is_event_day:
            session.finish(event_standdown=True)
            return 0

    print(f"[live] session {day} | shakedown={shakedown} | chain={chain.available} "
          f"| CONFIG_HASH {cfg.config_hash[:12]}…")
    while True:
        now = dt.datetime.now(ET)
        now_min = now.hour * 60 + now.minute
        if now_min >= cfg.i("r5_clock", "session_end_min"):
            session.finish()
            print("[live] 16:00 — session closed")
            return 0
        # wait for the next minute boundary + 2s (bar completion + vendor lag)
        time.sleep(max(0.2, 62 - now.second - now.microsecond / 1e6)
                   if now.second < 2 else max(0.2, 60 - now.second + 2))
        t0 = time.monotonic()
        try:
            spx = spx_bars_today(day)
        except Exception as e:
            print(f"[live] SPX pull failed: {e}")
            continue
        try:
            hframe = hiro.frame(day)
        except Exception as e:
            print(f"[live] HIRO pull failed: {e}")
            hframe = None
        try:
            spy = spy_bars_today(day)
            spy_map = {int(r.min): SpyBar(int(r.min), r.open, r.high, r.low,
                                          r.close, r.volume) for r in spy.itertuples()}
        except Exception:
            spy_map = {}
        now_min = dt.datetime.now(ET).hour * 60 + dt.datetime.now(ET).minute
        new = spx[(spx["min"] > processed_min) & (spx["min"] < now_min)
                  & (spx["min"] >= 570) & (spx["min"] <= 960)]
        for r in new.itertuples():
            m = int(r.min)
            tick = ReplayTick(Bar(m, r.open, r.high, r.low, r.close), spy_map.get(m),
                              hframe[hframe["min"] <= m] if hframe is not None else None)
            session.process_tick(tick)
            processed_min = m
        lat = time.monotonic() - t0
        if lat > 5.0:
            log.emit(session._stamp([Event(event_type="state_line", rule_id="NFR",
                                           notes=f"latency {lat:.1f}s > 5s budget")],
                                    processed_min))
