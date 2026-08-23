"""Live plumbing (task 7): ThetaData Python SDK SPX/SPY bars (v3 SDK,
creds-file auth direct to ThetaData — NO local terminal), HIRO snapshot via the
logged-in Chrome CDP session (IMPORTED from HIRO_finder — not copied, DRY
ledger), optional Schwab chain adapter, and the live session loop.

Requires: ~/Dev/ThetaData/creds.txt; Chrome with --remote-debugging-port=9222
logged in to dashboard.spotgamma.com.
Note: SPY stock history needs a paid ThetaData stock tier — on the current
index-only subscription the SDK returns PERMISSION_DENIED and the engine runs
the spec'd DEGRADED_VWAP path (R3.4 -> CHOP), logged once per session.
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

from .config import REPO_ROOT, Config
from .eventlog import EventLog
from .feeds import ReplayTick, hiro_minute_frame
from .models import Bar, Event, SpyBar, TIER_FULL
from .session import Session, build_range60_history

ET = ZoneInfo("America/New_York")
THETA_CREDS = Path("~/Dev/ThetaData/creds.txt").expanduser()
HIRO_FINDER = Path("~/Dev/HIRO_finder").expanduser()
SYMBOL = "S&P 500"
CDP_PORT = 9222


# ---------------------------------------------------------------------------
# ThetaData (R2.1 / R2.6) via the Python SDK (project convention — see
# scripts/fetch_nvda_1m.py): ThetaClient(creds_file=...) talks directly to
# ThetaData; re-request today's history each minute — stateless, self-healing.
# ---------------------------------------------------------------------------
_theta_client = None
PULL_TIMEOUT_S = 8.0


def theta_client():
    global _theta_client
    if _theta_client is None:
        from thetadata import ThetaClient
        _theta_client = ThetaClient(creds_file=str(THETA_CREDS))
    return _theta_client


def reset_theta_client() -> None:
    """Drop the singleton so the next call re-authenticates (the SDK holds a
    session token with no re-auth logic — red-team 2026-08-23 finding 2)."""
    global _theta_client
    _theta_client = None


def _pull(fn, *args, **kwargs):
    """Run an SDK call with a hard timeout (gRPC has none — finding 1). On
    timeout or error: reset the client and raise; the caller's per-minute loop
    retries next cycle with a fresh session."""
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as _TO
    ex = ThreadPoolExecutor(max_workers=1)
    try:
        fut = ex.submit(fn, *args, **kwargs)
        return fut.result(timeout=PULL_TIMEOUT_S)
    except _TO:
        reset_theta_client()
        raise TimeoutError(f"ThetaData pull exceeded {PULL_TIMEOUT_S}s")
    except Exception:
        reset_theta_client()
        raise
    finally:
        ex.shutdown(wait=False)


def _to_min_frame(resp, keep_volume: bool = False) -> pd.DataFrame:
    df = resp.to_pandas() if hasattr(resp, "to_pandas") else pd.DataFrame(resp)
    ts = pd.to_datetime(df.timestamp)
    df["min"] = (ts.dt.hour * 60 + ts.dt.minute).astype(int)
    cols = ["min", "open", "high", "low", "close"] + (["volume"] if keep_volume else [])
    return df[cols]


def spx_bars_today(day: str) -> pd.DataFrame:
    """Completed SPX 1-min bars for `day`, columns min/open/high/low/close."""
    d = dt.date.fromisoformat(day)
    resp = _pull(theta_client().index_history_ohlc, symbol="SPX",
                 start_date=d, end_date=d, interval="1m")
    return _to_min_frame(resp)


_spy_denied = False


def spy_bars_today(day: str) -> pd.DataFrame:
    """SPY 1-min OHLCV. Needs a ThetaData stock subscription; PERMISSION_DENIED
    -> empty frame (engine degrades per R3.4/R10, logged as DEGRADED_VWAP)."""
    global _spy_denied
    if _spy_denied:
        return pd.DataFrame(columns=["min", "open", "high", "low", "close", "volume"])
    d = dt.date.fromisoformat(day)
    try:
        resp = _pull(theta_client().stock_history_ohlc, symbol="SPY", interval="1m",
                     start_date=d, end_date=d)
        return _to_min_frame(resp, keep_volume=True)
    except Exception as e:
        # latch ONLY on the explicit subscription-tier message; transient
        # auth/session PERMISSION_DENIEDs must not kill VWAP for the day
        msg = str(e).lower()
        if "subscription" in msg and ("free" in msg or "value" in msg or "upgrad" in msg):
            _spy_denied = True
            print("[live] SPY history not in the ThetaData subscription — "
                  "running DEGRADED_VWAP (context reads = CHOP)")
            return pd.DataFrame(columns=["min", "open", "high", "low", "close", "volume"])
        raise


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
        # last minute that actually made it into the log — bars after it
        # completed during downtime and MUST be processed live (logged), never muted
        today_rows = prior[prior.session_date == day]
        logged_ts = today_rows.ts.dropna().astype(str)
        logged_mins = [int(t[-5:-3]) * 60 + int(t[-2:]) for t in logged_ts
                       if len(t) >= 5 and t[-5:-3].isdigit() and t[-2:].isdigit()]
        last_logged = max(logged_mins) if logged_mins else 569
        print(f"[resume] warm replaying through last logged bar "
              f"{last_logged // 60:02d}:{last_logged % 60:02d}…")
        spx = spx_bars_today(day)
        spy = spy_bars_today(day)
        hframe = hiro.frame(day)
        spy_map = {int(r.min): SpyBar(int(r.min), r.open, r.high, r.low, r.close, r.volume)
                   for r in spy.itertuples()}
        warm, catchup = [], []
        for r in spx.itertuples():
            m = int(r.min)
            if 570 <= m <= 960:
                t = ReplayTick(Bar(m, r.open, r.high, r.low, r.close),
                               spy_map.get(m), hframe[hframe["min"] <= m])
                (warm if m <= last_logged else catchup).append(t)
        session.warm_replay(warm)
        for t in catchup:                      # downtime bars: evaluated AND logged
            session.process_tick(t)
        processed_min = session.last_bar_min or 569
        print(f"[resume] state rebuilt through {processed_min // 60:02d}:{processed_min % 60:02d} "
              f"({len(catchup)} downtime bar(s) processed live)")
    else:
        log.emit(session._stamp(session.startup_events(), None))
        if session.calendar.is_event_day:
            session.finish(event_standdown=True)
            return 0

    if not chain.available:
        log.emit(session._stamp([Event(event_type="banner", rule_id="R2.5",
            notes="NO CHAIN FEED — proxy mode: strike hints only, cap = 15-pt spot "
                  "proxy, 15:30 always resolution_close, IM missing -> context CHOP")],
            None))
    print(f"[live] session {day} | shakedown={shakedown} | chain={chain.available} "
          f"| CONFIG_HASH {cfg.config_hash[:12]}…")
    while True:
        now = dt.datetime.now(ET)
        now_min = now.hour * 60 + now.minute
        if now_min > cfg.i("r5_clock", "session_end_min"):
            # > 960: the 16:00 bar has completed — final catch-up matches the
            # backtest grid (570..960), one code path (red-team finding 3)
            try:
                spx = spx_bars_today(day)
            except Exception as e:
                print(f"[live] final catch-up SPX failed: {e}")
                spx = None
            if spx is not None:
                try:
                    hframe = hiro.frame(day)
                except Exception as e:
                    print(f"[live] final catch-up HIRO failed: {e}")
                    hframe = None
                try:
                    spy = spy_bars_today(day)
                    spy_map = {int(r.min): SpyBar(int(r.min), r.open, r.high, r.low,
                                                  r.close, r.volume) for r in spy.itertuples()}
                except Exception:
                    spy_map = {}
                tail = spx[(spx["min"] > processed_min) & (spx["min"] <= 960)]
                for r in tail.itertuples():
                    m = int(r.min)
                    session.process_tick(ReplayTick(
                        Bar(m, r.open, r.high, r.low, r.close), spy_map.get(m),
                        hframe[hframe["min"] <= m] if hframe is not None else None))
                    processed_min = m
            session.finish()
            print("[live] 16:00 — session closed")
            return 0
        # wait for the next minute boundary + 2s (bar completion + vendor lag)
        time.sleep(max(0.2, 62 - now.second - now.microsecond / 1e6)
                   if now.second < 2 else max(0.2, 60 - now.second + 2))
        t0 = time.monotonic()
        cutoff_min = dt.datetime.now(ET).hour * 60 + dt.datetime.now(ET).minute
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
        new = spx[(spx["min"] > processed_min) & (spx["min"] < cutoff_min)
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
