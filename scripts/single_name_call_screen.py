#!/usr/bin/env python3
"""Screen liquid single stocks for NVDA-like call-side delta-bomb setups.

The screen has two independent branches, both frozen from the NVDA research:

* buy-first: calls are cheap after a pullback, so buy a 30--60 DTE call or
  far-OTM call spread before the rebound;
* sell-first: the front 5-delta call wing is unusually rich and kinked, so
  sell the far weekly call and rest a bid for the nearer call after the crush.

ORATS acquisition is point-in-time and resumable.  Every HTTP attempt is
recorded before it is made, and the run refuses to exceed the configured call
budget.  Secrets are never included in URLs written to logs or manifests.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
import gzip
import json
import logging
import math
import os
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv


LOG = logging.getLogger("single_name_call_screen")
ORATS_BASE_URL = "https://api.orats.io/datav2"
DEFAULT_START = "2026-08-12"
DEFAULT_END = "2026-08-21"
DEFAULT_CACHE = Path("/private/tmp/delta_bomb_single_name_call_screen_20260823")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "replay"
MAX_TICKERS_PER_CALL = 10
MIN_HISTORY = 126
LOOKBACK = 252

SUMMARY_FIELDS = (
    "ticker",
    "tradeDate",
    "stockPrice",
    "iv10d",
    "iv30d",
    "iv90d",
    "dlt5Iv10d",
    "dlt95Iv10d",
    "dlt5Iv30d",
    "dlt95Iv30d",
    "exErnIv30d",
    "exErnDlt25Iv30d",
    "exErnDlt75Iv30d",
    "ieeEarnEffect",
    "confidence",
    "mwAdj30",
)
CORE_FIELDS = (
    "ticker",
    "tradeDate",
    "priorCls",
    "stkVolu",
    "avgOptVolu20d",
    "oi",
    "mktCap",
    "sector",
    "sectorName",
    "bestEtf",
    "confidence",
    "mktWidthVol",
    "nextErn",
    "wksNextErn",
    "ivPctile1y",
    "ivPctile1m",
)
IVRANK_FIELDS = (
    "ticker",
    "tradeDate",
    "ivRank1y",
    "ivPct1y",
    "ivRank1m",
    "ivPct1m",
)
STRIKE_FIELDS = (
    "ticker",
    "tradeDate",
    "expirDate",
    "dte",
    "strike",
    "stockPrice",
    "delta",
    "smvVol",
    "callValue",
    "callBidPrice",
    "callAskPrice",
    "callBidIv",
    "callMidIv",
    "callAskIv",
    "callVolume",
    "callOpenInterest",
)
VOL_FIELDS = (
    "iv10d",
    "iv30d",
    "iv90d",
    "dlt5Iv10d",
    "dlt95Iv10d",
    "dlt5Iv30d",
    "dlt95Iv30d",
    "exErnIv30d",
    "exErnDlt25Iv30d",
    "exErnDlt75Iv30d",
)
EQUITY_SECTORS = frozenset(
    {
        "Technology",
        "C. Cyclical",
        "C. Defensive",
        "Industrials",
        "Healthcare",
        "Financials",
        "Energy",
        "Comm",
        "Utilities",
        "Real Estate",
        "Materials",
    }
)
NON_STOCK_TICKERS = frozenset({"DJX", "NDX", "NQX", "OEX", "RUT", "SPX", "VIX", "XSP"})


class CallBudgetExceeded(RuntimeError):
    """Raised before an ORATS call would exceed the approved budget."""


def prior_percentile(
    history: np.ndarray,
    current: float,
    *,
    min_observations: int = MIN_HISTORY,
) -> float:
    """Return the share of finite prior observations strictly below current."""
    finite = np.asarray(history, dtype=float)
    finite = finite[np.isfinite(finite)]
    if len(finite) < min_observations or not np.isfinite(current):
        return math.nan
    return float(np.mean(finite < current) * 100.0)


def buy_first_tier(
    iv_rank_1y: float,
    rr25_percentile: float,
    call_skew_percentile: float,
    call_wing_30_vol_points: float,
    normal_contango: bool,
) -> str:
    """Apply the pre-registered Good/Better/Best buy-first surface tiers."""
    if (
        iv_rank_1y <= 25
        and rr25_percentile >= 90
        and call_skew_percentile <= 10
        and call_wing_30_vol_points <= 1
        and normal_contango
    ):
        return "best"
    if (
        iv_rank_1y <= 35
        and rr25_percentile >= 80
        and call_skew_percentile <= 25
        and call_wing_30_vol_points <= 2
    ):
        return "better"
    if (
        iv_rank_1y <= 50
        and rr25_percentile >= 60
        and call_skew_percentile <= 40
        and call_wing_30_vol_points <= 3
    ):
        return "good"
    return ""


def sell_first_archetype(
    call_wing_10_percentile: float,
    call_kink_percentile: float,
    rr25_percentile: float,
    put_wing_10_percentile: float,
    iv10_percentile: float,
    spot_return_5d_percent: float,
) -> str:
    """Classify a sell-first tell as grab, post-shock smile, other, or none."""
    if call_wing_10_percentile < 85 or call_kink_percentile < 70:
        return ""
    if (
        rr25_percentile <= 10
        and put_wing_10_percentile < 70
        and spot_return_5d_percent > 0
    ):
        return "grab"
    if put_wing_10_percentile >= 85 and iv10_percentile >= 80:
        return "post-shock smile"
    return "other"


def sell_first_is_actionable(
    archetype: str,
    drawdown_20d_percent: float,
    iv_rank_1y: float,
    earnings_near_front_expiry: bool,
) -> bool:
    """Apply the non-surface regime and event gates to a sell-first tell."""
    if earnings_near_front_expiry:
        return False
    if archetype == "grab":
        return drawdown_20d_percent >= -5 and 30 <= iv_rank_1y <= 70
    return archetype == "post-shock smile"


def is_single_stock_ticker(ticker: str) -> bool:
    """Reject ORATS index symbols and synthetic ``*_C`` aliases."""
    return bool(ticker) and "_" not in ticker and ticker not in NON_STOCK_TICKERS


def read_ticker_universe(path: Path) -> frozenset[str]:
    """Read and validate a ticker-universe CSV."""
    if not path.is_file():
        raise FileNotFoundError(f"ticker universe does not exist: {path}")
    frame = pd.read_csv(path)
    ticker_columns = [column for column in frame.columns if column.lower() == "ticker"]
    if len(ticker_columns) != 1:
        raise ValueError(f"ticker universe must contain exactly one Ticker column: {path}")
    tickers = frozenset(
        frame[ticker_columns[0]].dropna().astype(str).str.strip().str.upper()
    ) - {""}
    if not tickers:
        raise ValueError(f"ticker universe is empty: {path}")
    return tickers


def chunks(items: list[str], size: int = MAX_TICKERS_PER_CALL) -> Iterable[list[str]]:
    """Yield ticker chunks while enforcing the ORATS ten-ticker ceiling."""
    if size < 1 or size > MAX_TICKERS_PER_CALL:
        raise ValueError(f"batch size must be in [1, {MAX_TICKERS_PER_CALL}]")
    for index in range(0, len(items), size):
        yield items[index : index + size]


def read_gzip_json(path: Path) -> list[dict[str, Any]]:
    """Read one cached ORATS data payload."""
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise TypeError(f"expected list payload in {path}")
    return data


def write_gzip_json(path: Path, rows: list[dict[str, Any]]) -> None:
    """Atomically cache one ORATS data payload."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8") as handle:
        json.dump(rows, handle, separators=(",", ":"))
    temporary.replace(path)


@dataclass
class CallLedger:
    """Persistent hard guard around the user-approved ORATS call budget."""

    path: Path
    max_calls: int
    initial_used: int

    def __post_init__(self) -> None:
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            self.data: dict[str, Any] = {
                "max_calls": self.max_calls,
                "used": self.initial_used,
                "initial_used": self.initial_used,
                "attempts": [],
            }
            self.save()
        if int(self.data["max_calls"]) != self.max_calls:
            raise ValueError("existing manifest call budget differs from --max-calls")

    @property
    def used(self) -> int:
        """Return HTTP attempts consumed, including prior probes and retries."""
        return int(self.data["used"])

    def record_attempt(self, endpoint: str, safe_params: dict[str, str]) -> None:
        """Record an attempt before network I/O, failing before budget overrun."""
        if self.used >= self.max_calls:
            raise CallBudgetExceeded(
                f"ORATS budget exhausted: {self.used}/{self.max_calls} calls used"
            )
        self.data["used"] = self.used + 1
        self.data["attempts"].append(
            {
                "at": datetime.now(UTC).isoformat(),
                "endpoint": endpoint,
                "params": safe_params,
            }
        )
        self.save()

    def save(self) -> None:
        """Persist the ledger atomically."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, indent=2))
        temporary.replace(self.path)


class RollingRateLimiter:
    """Limit request starts to a maximum count in each rolling minute."""

    def __init__(self, requests_per_minute: int) -> None:
        if requests_per_minute < 1:
            raise ValueError("requests_per_minute must be positive")
        self.requests_per_minute = requests_per_minute
        self.timestamps: list[float] = []

    def wait(self) -> None:
        """Block only until the oldest request falls outside the minute."""
        now = time.monotonic()
        self.timestamps = [stamp for stamp in self.timestamps if now - stamp < 60]
        if len(self.timestamps) >= self.requests_per_minute:
            delay = 60 - (now - self.timestamps[0]) + 0.1
            time.sleep(max(delay, 0))
        self.timestamps.append(time.monotonic())


class OratsClient:
    """Small authenticated ORATS client with retries, budget, and rate limits."""

    def __init__(
        self,
        token: str,
        ledger: CallLedger,
        requests_per_minute: int,
    ) -> None:
        if not token:
            raise ValueError("ORATS_API_KEY is empty")
        self.token = token
        self.ledger = ledger
        self.limiter = RollingRateLimiter(requests_per_minute)
        self.session = requests.Session()
        self.session.headers.update({"Accept-Encoding": "gzip"})

    def get(
        self,
        endpoint: str,
        params: dict[str, str],
        *,
        timeout: int = 300,
        max_attempts: int = 3,
    ) -> list[dict[str, Any]]:
        """Fetch an ORATS data array without ever logging its auth token."""
        safe_params = dict(params)
        for attempt in range(1, max_attempts + 1):
            self.limiter.wait()
            self.ledger.record_attempt(endpoint, safe_params)
            try:
                response = self.session.get(
                    f"{ORATS_BASE_URL}/{endpoint}",
                    params={**params, "token": self.token},
                    timeout=timeout,
                )
            except requests.RequestException as error:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"ORATS connection failure for {endpoint} after {attempt} attempts"
                    ) from error
                time.sleep(2**attempt)
                continue
            if response.status_code in {429, 500, 502, 503, 504} and attempt < max_attempts:
                time.sleep(2**attempt)
                continue
            if response.status_code >= 400:
                raise RuntimeError(
                    f"ORATS HTTP {response.status_code} for {endpoint}; response omitted"
                )
            payload = response.json()
            rows = payload.get("data", [])
            if not isinstance(rows, list):
                raise TypeError(f"ORATS returned non-list data for {endpoint}")
            return rows
        raise AssertionError("unreachable")


def cache_path(cache_dir: Path, endpoint: str, trade_date: str) -> Path:
    """Return the deterministic cache path for one endpoint/date payload."""
    return cache_dir / endpoint.replace("/", "_") / f"{trade_date}.json.gz"


def batch_history_cache_path(
    cache_dir: Path,
    endpoint: str,
    tickers: Iterable[str],
) -> Path:
    """Return the deterministic cache path for one full-history ticker batch."""
    batch_key = "-".join(sorted(set(tickers)))
    if not batch_key:
        raise ValueError("full-history ticker batch cannot be empty")
    return cache_dir / f"{endpoint.replace('/', '_')}_full" / f"{batch_key}.json.gz"


def fetch_to_cache(
    client: OratsClient,
    cache_dir: Path,
    endpoint: str,
    trade_date: str,
    fields: tuple[str, ...],
) -> tuple[Path, bool, int]:
    """Fetch one all-ticker daily snapshot unless it is already cached."""
    path = cache_path(cache_dir, endpoint, trade_date)
    if path.exists():
        rows = read_gzip_json(path)
        return path, False, len(rows)
    rows = client.get(
        endpoint,
        {"tradeDate": trade_date, "fields": ",".join(fields)},
    )
    if not rows:
        raise RuntimeError(f"empty ORATS response for {endpoint} on {trade_date}")
    write_gzip_json(path, rows)
    return path, True, len(rows)


def fetch_batch_history_to_cache(
    client: OratsClient,
    cache_dir: Path,
    endpoint: str,
    tickers: Iterable[str],
    fields: tuple[str, ...],
) -> tuple[Path, bool, int]:
    """Fetch a ten-ticker full history unless that exact batch is cached."""
    batch = sorted(set(tickers))
    if not 1 <= len(batch) <= MAX_TICKERS_PER_CALL:
        raise ValueError(
            f"full-history batch must contain 1-{MAX_TICKERS_PER_CALL} tickers"
        )
    path = batch_history_cache_path(cache_dir, endpoint, batch)
    if path.exists():
        rows = read_gzip_json(path)
        return path, False, len(rows)
    rows = client.get(
        endpoint,
        {"ticker": ",".join(batch), "fields": ",".join(fields)},
    )
    if not rows:
        raise RuntimeError(f"empty ORATS full-history response for {endpoint}: {batch}")
    write_gzip_json(path, rows)
    return path, True, len(rows)


def get_trading_dates(client: OratsClient, cache_dir: Path, end: str) -> list[str]:
    """Load the actual ORATS SPY trading calendar through end."""
    path = cache_dir / "hist_dailies" / "SPY_full_history.json.gz"
    if path.exists():
        rows = read_gzip_json(path)
    else:
        rows = client.get(
            "hist/dailies",
            {"ticker": "SPY", "fields": "ticker,tradeDate,clsPx"},
        )
        write_gzip_json(path, rows)

    def dates_through(payload: list[dict[str, Any]]) -> list[str]:
        return sorted(
            {
                str(row["tradeDate"])[:10]
                for row in payload
                if row.get("tradeDate") and str(row["tradeDate"])[:10] <= end
            }
        )

    dates = dates_through(rows)
    if end not in dates and path.exists():
        LOG.info("refreshing stale SPY trading calendar through %s", end)
        rows = client.get(
            "hist/dailies",
            {"ticker": "SPY", "fields": "ticker,tradeDate,clsPx"},
        )
        write_gzip_json(path, rows)
        dates = dates_through(rows)
    if end not in dates:
        raise ValueError(f"{end} is not an ORATS SPY trading date")
    return dates


def command_fetch(args: argparse.Namespace) -> None:
    """Fetch the trailing signal history and target-date liquidity snapshots."""
    env_path = Path(args.env_file).expanduser()
    if env_path.exists():
        load_dotenv(env_path)
    token = os.environ.get("ORATS_API_KEY", "")
    ledger = CallLedger(
        Path(args.cache_dir) / "manifest.json",
        max_calls=args.max_calls,
        initial_used=args.initial_used,
    )
    client = OratsClient(token, ledger, args.rpm)
    all_dates = get_trading_dates(client, Path(args.cache_dir), args.end)
    start_index = all_dates.index(args.start)
    end_index = all_dates.index(args.end)
    history_start_index = max(0, start_index - LOOKBACK)
    summary_dates = all_dates[history_start_index : end_index + 1]
    target_dates = all_dates[start_index : end_index + 1]
    ticker_universe = (
        sorted(read_ticker_universe(Path(args.universe_csv).expanduser()))
        if args.universe_csv
        else []
    )
    LOG.info(
        "summary dates=%d (%s..%s), target dates=%d, calls used=%d/%d",
        len(summary_dates),
        summary_dates[0],
        summary_dates[-1],
        len(target_dates),
        ledger.used,
        ledger.max_calls,
    )

    if ticker_universe:
        summary_batches = list(chunks(ticker_universe))
        for index, batch in enumerate(summary_batches, start=1):
            _, fetched, rows = fetch_batch_history_to_cache(
                client,
                Path(args.cache_dir),
                "hist/summaries",
                batch,
                SUMMARY_FIELDS,
            )
            LOG.info(
                "summary histories %d/%d tickers=%d rows=%d %s calls=%d/%d",
                index,
                len(summary_batches),
                len(batch),
                rows,
                "fetched" if fetched else "cached",
                ledger.used,
                ledger.max_calls,
            )
    else:
        for index, trade_date in enumerate(summary_dates, start=1):
            _, fetched, rows = fetch_to_cache(
                client,
                Path(args.cache_dir),
                "hist/summaries",
                trade_date,
                SUMMARY_FIELDS,
            )
            LOG.info(
                "summaries %d/%d %s rows=%d %s calls=%d/%d",
                index,
                len(summary_dates),
                trade_date,
                rows,
                "fetched" if fetched else "cached",
                ledger.used,
                ledger.max_calls,
            )

    for endpoint, fields in (("hist/cores", CORE_FIELDS), ("hist/ivrank", IVRANK_FIELDS)):
        for index, trade_date in enumerate(target_dates, start=1):
            _, fetched, rows = fetch_to_cache(
                client,
                Path(args.cache_dir),
                endpoint,
                trade_date,
                fields,
            )
            LOG.info(
                "%s %d/%d %s rows=%d %s calls=%d/%d",
                endpoint,
                index,
                len(target_dates),
                trade_date,
                rows,
                "fetched" if fetched else "cached",
                ledger.used,
                ledger.max_calls,
            )


def command_fetch_chains(args: argparse.Namespace) -> None:
    """Fetch filtered chains and earnings for every liquid surface candidate."""
    env_path = Path(args.env_file).expanduser()
    if env_path.exists():
        load_dotenv(env_path)
    token = os.environ.get("ORATS_API_KEY", "")
    cache_dir = Path(args.cache_dir)
    ledger = CallLedger(
        cache_dir / "manifest.json",
        max_calls=args.max_calls,
        initial_used=args.initial_used,
    )
    client = OratsClient(token, ledger, args.rpm)
    candidates_path = Path(args.output_dir) / "single_name_call_screen_candidates.csv"
    candidates = pd.read_csv(candidates_path)
    all_tickers = sorted(set(candidates["ticker"].astype(str)))
    for trade_date, day in candidates.groupby("tradeDate", sort=True):
        tickers = sorted(set(day["ticker"].astype(str)))
        batches = list(chunks(tickers))
        for index, batch in enumerate(batches, start=1):
            batch_key = "-".join(batch)
            path = cache_dir / "hist_strikes" / trade_date / f"{batch_key}.json.gz"
            if path.exists():
                rows = read_gzip_json(path)
                fetched = False
            else:
                rows = client.get(
                    "hist/strikes",
                    {
                        "ticker": ",".join(batch),
                        "tradeDate": trade_date,
                        "dte": "5,90",
                        "delta": ".005,.60",
                        "fields": ",".join(STRIKE_FIELDS),
                    },
                )
                write_gzip_json(path, rows)
                fetched = True
            LOG.info(
                "strikes %s batch %d/%d tickers=%d rows=%d %s calls=%d/%d",
                trade_date,
                index,
                len(batches),
                len(batch),
                len(rows),
                "fetched" if fetched else "cached",
                ledger.used,
                ledger.max_calls,
            )

    earnings_batches = list(chunks(all_tickers))
    for index, batch in enumerate(earnings_batches, start=1):
        batch_key = "-".join(batch)
        path = cache_dir / "hist_earnings" / f"{batch_key}.json.gz"
        if path.exists():
            rows = read_gzip_json(path)
            fetched = False
        else:
            rows = client.get(
                "hist/earnings",
                {
                    "ticker": ",".join(batch),
                    "fields": "ticker,earnDate,anncTod",
                },
            )
            write_gzip_json(path, rows)
            fetched = True
        LOG.info(
            "earnings batch %d/%d tickers=%d rows=%d %s calls=%d/%d",
            index,
            len(earnings_batches),
            len(batch),
            len(rows),
            "fetched" if fetched else "cached",
            ledger.used,
            ledger.max_calls,
        )


def command_fetch_followups(args: argparse.Namespace) -> None:
    """Fetch end-of-day chains after each finalist signal through the end date."""
    env_path = Path(args.env_file).expanduser()
    if env_path.exists():
        load_dotenv(env_path)
    token = os.environ.get("ORATS_API_KEY", "")
    cache_dir = Path(args.cache_dir)
    ledger = CallLedger(
        cache_dir / "manifest.json",
        max_calls=args.max_calls,
        initial_used=args.initial_used,
    )
    client = OratsClient(token, ledger, args.rpm)
    finalists_path = Path(args.output_dir) / "single_name_call_screen_finalists.csv"
    finalists = pd.read_csv(finalists_path)
    trading_dates = get_trading_dates(client, cache_dir, args.end)
    target_dates = [date for date in trading_dates if args.start <= date <= args.end]
    for trade_date in target_dates:
        active_finalists = finalists[finalists["tradeDate"] < trade_date]
        tickers = sorted(
            set(
                active_finalists["ticker"].astype(str)
            )
        )
        batches = list(chunks(tickers))
        for index, batch in enumerate(batches, start=1):
            batch_key = "-".join(batch)
            path = cache_dir / "hist_followup_strikes" / trade_date / f"{batch_key}.json.gz"
            if path.exists():
                rows = read_gzip_json(path)
                fetched = False
            else:
                rows = client.get(
                    "hist/strikes",
                    {
                        "ticker": ",".join(batch),
                        "tradeDate": trade_date,
                        "dte": "1,90",
                        "delta": ".005,.60",
                        "fields": ",".join(STRIKE_FIELDS),
                    },
                )
                write_gzip_json(path, rows)
                fetched = True
            LOG.info(
                "followups %s batch %d/%d tickers=%d rows=%d %s calls=%d/%d",
                trade_date,
                index,
                len(batches),
                len(batch),
                len(rows),
                "fetched" if fetched else "cached",
                ledger.used,
                ledger.max_calls,
            )

        date_rows = load_all_gzip_rows(cache_dir / "hist_followup_strikes" / trade_date)
        missing_tickers: list[str] = []
        for _, finalist in active_finalists.iterrows():
            contract_rows = date_rows[
                (date_rows["ticker"] == finalist["ticker"])
                & (date_rows["expirDate"].astype(str) == str(finalist["expiry"]))
                & date_rows["strike"].isin(
                    [float(finalist["leg1_strike"]), float(finalist["leg2_strike"])]
                )
            ]
            if contract_rows["strike"].nunique() < 2:
                missing_tickers.append(str(finalist["ticker"]))
        missing_batches = list(chunks(sorted(set(missing_tickers))))
        for index, batch in enumerate(missing_batches, start=1):
            batch_key = "-".join(batch)
            path = (
                cache_dir
                / "hist_followup_strikes_unfiltered"
                / trade_date
                / f"{batch_key}.json.gz"
            )
            if path.exists():
                rows = read_gzip_json(path)
                fetched = False
            else:
                rows = client.get(
                    "hist/strikes",
                    {
                        "ticker": ",".join(batch),
                        "tradeDate": trade_date,
                        "dte": "1,90",
                        "fields": ",".join(STRIKE_FIELDS),
                    },
                )
                write_gzip_json(path, rows)
                fetched = True
            LOG.info(
                "unfiltered followups %s batch %d/%d tickers=%d rows=%d %s calls=%d/%d",
                trade_date,
                index,
                len(missing_batches),
                len(batch),
                len(rows),
                "fetched" if fetched else "cached",
                ledger.used,
                ledger.max_calls,
            )


def numeric(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    """Convert present columns to numeric in place."""
    present = [column for column in columns if column in frame]
    frame[present] = frame[present].apply(pd.to_numeric, errors="coerce")


def empty_contract(reason: str) -> dict[str, Any]:
    """Return a stable failed-selection record."""
    return {
        "chain_confirmed": False,
        "failure_reason": reason,
        "expiry": "",
        "dte": math.nan,
        "leg1_action": "",
        "leg1_strike": math.nan,
        "leg1_delta": math.nan,
        "leg1_bid": math.nan,
        "leg1_ask": math.nan,
        "leg1_oi": math.nan,
        "leg1_volume": math.nan,
        "leg2_action": "",
        "leg2_strike": math.nan,
        "leg2_bid": math.nan,
        "leg2_ask": math.nan,
        "leg2_oi": math.nan,
        "leg2_volume": math.nan,
        "spread_width": math.nan,
        "entry_cash": math.nan,
        "target_leg2_price": math.nan,
        "contract_wing_iv_points": math.nan,
        "event_inside_expiry": False,
    }


def quote_width(row: pd.Series) -> float:
    """Return ask minus bid for one call quote."""
    return float(row["callAskPrice"] - row["callBidPrice"])


def contract_record(
    leg1: pd.Series,
    leg2: pd.Series,
    *,
    leg1_action: str,
    leg2_action: str,
    entry_cash: float,
    target_leg2_price: float,
    contract_wing_iv_points: float,
    event_inside_expiry: bool,
    confirmed: bool,
    reasons: list[str],
) -> dict[str, Any]:
    """Create the common two-leg output schema."""
    return {
        "chain_confirmed": bool(confirmed),
        "failure_reason": "; ".join(reasons),
        "expiry": str(leg1["expirDate"]),
        "dte": int(leg1["dte"]),
        "leg1_action": leg1_action,
        "leg1_strike": float(leg1["strike"]),
        "leg1_delta": float(leg1["delta"]),
        "leg1_bid": float(leg1["callBidPrice"]),
        "leg1_ask": float(leg1["callAskPrice"]),
        "leg1_oi": int(leg1["callOpenInterest"]),
        "leg1_volume": int(leg1["callVolume"]),
        "leg2_action": leg2_action,
        "leg2_strike": float(leg2["strike"]),
        "leg2_bid": float(leg2["callBidPrice"]),
        "leg2_ask": float(leg2["callAskPrice"]),
        "leg2_oi": int(leg2["callOpenInterest"]),
        "leg2_volume": int(leg2["callVolume"]),
        "spread_width": abs(float(leg2["strike"] - leg1["strike"])),
        "entry_cash": float(entry_cash),
        "target_leg2_price": float(target_leg2_price),
        "contract_wing_iv_points": float(contract_wing_iv_points),
        "event_inside_expiry": bool(event_inside_expiry),
    }


def select_sell_contract(
    chain: pd.DataFrame,
    event_expiries: set[str],
) -> dict[str, Any]:
    """Select the nearest 5--12 DTE 4-delta short call and nearer call."""
    eligible = chain[
        chain["dte"].between(5, 19) & chain["delta"].between(0.02, 0.06)
    ].copy()
    if eligible.empty:
        return empty_contract("no 2-6 delta call in 5-19 DTE")
    preferred = eligible[eligible["dte"].between(5, 12)]
    pool = preferred if not preferred.empty else eligible
    selected_dte = int(pool["dte"].min())
    pool = pool[pool["dte"] == selected_dte]
    wing = pool.loc[(pool["delta"] - 0.04).abs().idxmin()]
    expiry = str(wing["expirDate"])
    expiry_rows = chain[chain["expirDate"].astype(str) == expiry]
    nearer_rows = expiry_rows[expiry_rows["strike"] < wing["strike"]]
    if nearer_rows.empty:
        return empty_contract("no nearer listed call strike")
    nearer = nearer_rows.loc[nearer_rows["strike"].idxmax()]
    atm = expiry_rows.loc[(expiry_rows["delta"] - 0.50).abs().idxmin()]
    wing_iv = float((wing["callMidIv"] - atm["callMidIv"]) * 100)
    event_inside = expiry in event_expiries
    reasons: list[str] = []
    if float(wing["callBidPrice"]) < 0.20:
        reasons.append("far-call bid below 0.20")
    if quote_width(wing) > 0.10 + 1e-9:
        reasons.append("far-call quote wider than 0.10")
    if int(wing["callOpenInterest"]) < 25:
        reasons.append("far-call OI below 25")
    if float(nearer["callAskPrice"]) <= 0:
        reasons.append("nearer call has no ask")
    if wing_iv < 2:
        reasons.append("selected call less than 2 vol points above ATM")
    if event_inside:
        reasons.append("earnings inside expiry")
    return contract_record(
        wing,
        nearer,
        leg1_action="STO",
        leg2_action="BTO",
        entry_cash=float(wing["callBidPrice"]),
        target_leg2_price=max(float(wing["callBidPrice"]) - 0.10, 0.10),
        contract_wing_iv_points=wing_iv,
        event_inside_expiry=event_inside,
        confirmed=not reasons,
        reasons=reasons,
    )


def select_standard_buy_contract(
    chain: pd.DataFrame,
    event_expiries: set[str],
) -> dict[str, Any]:
    """Select a 30--60 DTE 15-delta long call and next higher strike."""
    eligible = chain[
        chain["dte"].between(30, 60) & chain["delta"].between(0.10, 0.20)
    ].copy()
    if eligible.empty:
        return empty_contract("no 10-20 delta call in 30-60 DTE")
    expiries = (
        eligible[["expirDate", "dte"]]
        .drop_duplicates()
        .assign(
            has_event=lambda frame: frame["expirDate"].astype(str).isin(event_expiries),
            dte_distance=lambda frame: (frame["dte"] - 45).abs(),
        )
        .sort_values(["has_event", "dte_distance", "dte"])
    )
    expiry = str(expiries.iloc[0]["expirDate"])
    expiry_rows = chain[chain["expirDate"].astype(str) == expiry]
    long_pool = eligible[eligible["expirDate"].astype(str) == expiry]
    long_call = long_pool.loc[(long_pool["delta"] - 0.15).abs().idxmin()]
    upper_rows = expiry_rows[expiry_rows["strike"] > long_call["strike"]]
    if upper_rows.empty:
        return empty_contract("no higher listed call strike")
    upper = upper_rows.loc[upper_rows["strike"].idxmin()]
    event_inside = expiry in event_expiries
    reasons: list[str] = []
    if float(long_call["callBidPrice"]) <= 0 or float(long_call["callAskPrice"]) < 0.20:
        reasons.append("long call lacks a two-sided quote above 0.20")
    if quote_width(long_call) > 0.20 + 1e-9:
        reasons.append("long-call quote wider than 0.20")
    if int(long_call["callOpenInterest"]) < 25 or int(upper["callOpenInterest"]) < 25:
        reasons.append("one leg has OI below 25")
    if float(upper["callBidPrice"]) <= 0:
        reasons.append("upper call has no bid")
    if event_inside:
        reasons.append("earnings inside expiry")
    return contract_record(
        long_call,
        upper,
        leg1_action="BTO",
        leg2_action="STO",
        entry_cash=float(long_call["callAskPrice"]),
        target_leg2_price=float(long_call["callAskPrice"]) + 0.10,
        contract_wing_iv_points=math.nan,
        event_inside_expiry=event_inside,
        confirmed=not reasons,
        reasons=reasons,
    )


def select_puke_buy_spread(
    chain: pd.DataFrame,
    event_expiries: set[str],
) -> dict[str, Any]:
    """Select a cheap roughly $5-wide call spread 20--35% OTM, 30--90 DTE."""
    eligible = chain[chain["dte"].between(30, 90)].copy()
    eligible["otm_pct"] = (eligible["strike"] / eligible["stockPrice"] - 1) * 100
    lowers = eligible[eligible["otm_pct"].between(20, 35)]
    pairs: list[dict[str, Any]] = []
    for _, lower in lowers.iterrows():
        expiry = str(lower["expirDate"])
        upper_pool = eligible[
            (eligible["expirDate"].astype(str) == expiry)
            & (eligible["strike"] > lower["strike"])
        ].copy()
        upper_pool["width_distance"] = (
            (upper_pool["strike"] - float(lower["strike"])) - 5
        ).abs()
        upper_pool = upper_pool[
            (upper_pool["strike"] - float(lower["strike"])).between(2.5, 7.5)
        ]
        if upper_pool.empty:
            continue
        upper = upper_pool.sort_values(["width_distance", "strike"]).iloc[0]
        debit = float(lower["callAskPrice"] - upper["callBidPrice"])
        event_inside = expiry in event_expiries
        reasons: list[str] = []
        if not 0.05 <= debit <= 0.50:
            reasons.append("spread debit outside 0.05-0.50")
        if float(lower["callBidPrice"]) <= 0 or float(upper["callBidPrice"]) <= 0:
            reasons.append("one leg lacks a bid")
        if quote_width(lower) + quote_width(upper) > 0.20 + 1e-9:
            reasons.append("combined leg quote widths exceed 0.20")
        if int(lower["callOpenInterest"]) < 25 or int(upper["callOpenInterest"]) < 25:
            reasons.append("one leg has OI below 25")
        if event_inside:
            reasons.append("earnings inside expiry")
        record = contract_record(
            lower,
            upper,
            leg1_action="BTO",
            leg2_action="STO",
            entry_cash=debit,
            target_leg2_price=math.nan,
            contract_wing_iv_points=math.nan,
            event_inside_expiry=event_inside,
            confirmed=not reasons,
            reasons=reasons,
        )
        record["lower_otm_pct"] = float(lower["otm_pct"])
        record["selection_distance"] = abs(float(lower["otm_pct"]) - 27.5)
        pairs.append(record)
    if not pairs:
        return empty_contract("no roughly $5-wide spread 20-35% OTM in 30-90 DTE")
    pairs.sort(
        key=lambda row: (
            not row["chain_confirmed"],
            row["entry_cash"] if row["entry_cash"] > 0 else math.inf,
            row["selection_distance"],
            abs(row["dte"] - 45),
        )
    )
    return pairs[0]


def load_all_gzip_rows(directory: Path) -> pd.DataFrame:
    """Load every gzipped JSON-list cache below a directory."""
    frames = [pd.DataFrame(read_gzip_json(path)) for path in sorted(directory.rglob("*.json.gz"))]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def candidate_event_expiries(
    chain: pd.DataFrame,
    candidate: pd.Series,
    earnings: pd.DataFrame,
) -> set[str]:
    """Determine expiries containing known or ORATS-estimated next earnings."""
    signal_date = pd.Timestamp(candidate["tradeDate"])
    ticker_earnings = earnings[earnings["ticker"] == candidate["ticker"]].copy()
    ticker_earnings["earnDateParsed"] = pd.to_datetime(
        ticker_earnings["earnDate"], format="%Y-%m-%d", errors="coerce"
    )
    future_actual = ticker_earnings[
        ticker_earnings["earnDateParsed"] > signal_date
    ]["earnDateParsed"].sort_values()
    event_expiries: set[str] = set()
    expiry_rows = chain[["expirDate", "dte"]].drop_duplicates()
    for _, expiry_row in expiry_rows.iterrows():
        expiry = str(expiry_row["expirDate"])
        expiry_date = pd.Timestamp(expiry)
        if not future_actual.empty:
            event_inside = bool((future_actual <= expiry_date).any())
        else:
            weeks = pd.to_numeric(candidate.get("wksNextErn"), errors="coerce")
            event_inside = bool(
                pd.notna(weeks)
                and float(weeks) >= 0
                and int(expiry_row["dte"]) >= float(weeks) * 7
            )
        if event_inside:
            event_expiries.add(expiry)
    return event_expiries


def command_confirm(args: argparse.Namespace) -> None:
    """Select exact contracts and write chain-confirmed finalists."""
    cache_dir = Path(args.cache_dir)
    output_dir = Path(args.output_dir)
    candidates = pd.read_csv(output_dir / "single_name_call_screen_candidates.csv")
    chains_frame = load_all_gzip_rows(cache_dir / "hist_strikes")
    earnings = load_all_gzip_rows(cache_dir / "hist_earnings")
    if chains_frame.empty:
        raise FileNotFoundError("no cached strike chains; run fetch-chains first")
    numeric(
        chains_frame,
        (
            "dte",
            "strike",
            "stockPrice",
            "delta",
            "smvVol",
            "callValue",
            "callBidPrice",
            "callAskPrice",
            "callBidIv",
            "callMidIv",
            "callAskIv",
            "callVolume",
            "callOpenInterest",
        ),
    )
    chains_frame["tradeDate"] = pd.to_datetime(chains_frame["tradeDate"]).dt.strftime(
        "%Y-%m-%d"
    )
    confirmed_rows: list[dict[str, Any]] = []
    for _, candidate in candidates.iterrows():
        chain = chains_frame[
            (chains_frame["tradeDate"] == candidate["tradeDate"])
            & (chains_frame["ticker"] == candidate["ticker"])
        ].copy()
        if chain.empty:
            contract = empty_contract("no cached chain rows")
        else:
            event_expiries = candidate_event_expiries(chain, candidate, earnings)
            if candidate["scenario"] == "sell-first":
                contract = select_sell_contract(chain, event_expiries)
            elif candidate["scenario"] == "buy-first standard":
                contract = select_standard_buy_contract(chain, event_expiries)
            elif candidate["scenario"] == "buy-first puke":
                contract = select_puke_buy_spread(chain, event_expiries)
            else:
                contract = empty_contract(f"unsupported scenario: {candidate['scenario']}")
        confirmed_rows.append({**candidate.to_dict(), **contract})

    confirmations = pd.DataFrame(confirmed_rows)
    confirmations = confirmations.sort_values(
        ["scenario", "chain_confirmed", "ranking_score"],
        ascending=[True, False, False],
    )
    finalists = confirmations[confirmations["chain_confirmed"]].copy()
    finalists = finalists.sort_values("ranking_score", ascending=False).drop_duplicates(
        ["scenario", "ticker"], keep="first"
    )
    finalists = finalists.sort_values(
        ["scenario", "ranking_score"], ascending=[True, False]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    confirmations.to_csv(
        output_dir / "single_name_call_screen_chain_checks.csv", index=False
    )
    finalists.to_csv(output_dir / "single_name_call_screen_finalists.csv", index=False)
    chain_summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "candidate_rows": int(len(confirmations)),
        "confirmed_rows": int(confirmations["chain_confirmed"].sum()),
        "finalist_tickers": int(finalists["ticker"].nunique()),
        "confirmed_by_scenario": confirmations[
            confirmations["chain_confirmed"]
        ]["scenario"].value_counts().to_dict(),
        "unique_finalists_by_scenario": finalists["scenario"].value_counts().to_dict(),
        "failure_reasons": confirmations[
            ~confirmations["chain_confirmed"]
        ]["failure_reason"].value_counts().to_dict(),
    }
    (output_dir / "single_name_call_screen_chain_summary.json").write_text(
        json.dumps(chain_summary, indent=2)
    )
    LOG.info(
        "chain checks=%d confirmed=%d unique finalists=%d",
        len(confirmations),
        int(confirmations["chain_confirmed"].sum()),
        len(finalists),
    )


def command_evaluate(args: argparse.Namespace) -> None:
    """Mark each finalist on subsequent cached closes through the end date."""
    cache_dir = Path(args.cache_dir)
    output_dir = Path(args.output_dir)
    finalists = pd.read_csv(output_dir / "single_name_call_screen_finalists.csv")
    followups = pd.concat(
        [
            load_all_gzip_rows(cache_dir / "hist_followup_strikes"),
            load_all_gzip_rows(cache_dir / "hist_followup_strikes_unfiltered"),
        ],
        ignore_index=True,
    )
    if followups.empty:
        raise FileNotFoundError("no follow-up chains; run fetch-followups first")
    numeric(
        followups,
        (
            "strike",
            "stockPrice",
            "callBidPrice",
            "callAskPrice",
            "callVolume",
            "callOpenInterest",
        ),
    )
    followups["tradeDate"] = pd.to_datetime(followups["tradeDate"]).dt.strftime(
        "%Y-%m-%d"
    )
    all_signals = pd.read_parquet(output_dir / "single_name_call_screen_all.parquet")
    all_signals["tradeDate"] = pd.to_datetime(all_signals["tradeDate"]).dt.strftime(
        "%Y-%m-%d"
    )

    outcome_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    for _, finalist in finalists.iterrows():
        path = followups[
            (followups["ticker"] == finalist["ticker"])
            & (followups["tradeDate"] > finalist["tradeDate"])
            & (followups["expirDate"].astype(str) == str(finalist["expiry"]))
            & followups["strike"].isin(
                [float(finalist["leg1_strike"]), float(finalist["leg2_strike"])]
            )
        ].copy()
        daily: list[dict[str, Any]] = []
        for trade_date, day in path.groupby("tradeDate", sort=True):
            leg1_rows = day[day["strike"] == float(finalist["leg1_strike"])]
            leg2_rows = day[day["strike"] == float(finalist["leg2_strike"])]
            if leg1_rows.empty or leg2_rows.empty:
                continue
            leg1 = leg1_rows.iloc[0]
            leg2 = leg2_rows.iloc[0]
            if finalist["scenario"] == "sell-first":
                spread_bid = max(
                    float(leg2["callBidPrice"] - leg1["callAskPrice"]),
                    0.0,
                )
            else:
                spread_bid = max(
                    float(leg1["callBidPrice"] - leg2["callAskPrice"]),
                    0.0,
                )
            paired_close = False
            if finalist["scenario"] == "sell-first":
                paired_close = float(leg2["callAskPrice"]) <= float(
                    finalist["target_leg2_price"]
                )
                mark_value = float(finalist["entry_cash"] - leg1["callAskPrice"])
                multiple = math.nan
            elif finalist["scenario"] == "buy-first standard":
                paired_close = float(leg2["callBidPrice"]) >= float(
                    finalist["target_leg2_price"]
                )
                mark_value = float(leg1["callBidPrice"] - finalist["entry_cash"])
                multiple = math.nan
            else:
                mark_value = float(spread_bid - finalist["entry_cash"])
                multiple = (
                    spread_bid / float(finalist["entry_cash"])
                    if float(finalist["entry_cash"]) > 0
                    else math.nan
                )
            row = {
                "scenario": finalist["scenario"],
                "ticker": finalist["ticker"],
                "signal_date": finalist["tradeDate"],
                "tradeDate": trade_date,
                "stockPrice": float(leg1["stockPrice"]),
                "leg1_bid": float(leg1["callBidPrice"]),
                "leg1_ask": float(leg1["callAskPrice"]),
                "leg2_bid": float(leg2["callBidPrice"]),
                "leg2_ask": float(leg2["callAskPrice"]),
                "spread_bid": spread_bid,
                "paired_close_proxy": paired_close,
                "mark_value_per_share": mark_value,
                "mark_pnl_dollars": mark_value * 100,
                "spread_multiple": multiple,
            }
            daily.append(row)
            path_rows.append(row)

        if not daily:
            outcome_rows.append(
                {
                    **finalist.to_dict(),
                    "observed_status": "no follow-up mark",
                    "followup_sessions": 0,
                }
            )
            continue
        daily_frame = pd.DataFrame(daily)
        latest = daily[-1]
        pair_dates = daily_frame.loc[
            daily_frame["paired_close_proxy"], "tradeDate"
        ].tolist()
        breakout_tell = False
        if finalist["scenario"] == "sell-first":
            surface_path = all_signals[
                (all_signals["ticker"] == finalist["ticker"])
                & (all_signals["tradeDate"] > finalist["tradeDate"])
            ]
            breakout_tell = bool(
                (
                    (surface_path["stockPrice"] >= float(finalist["stockPrice"]) * 1.05)
                    & (
                        surface_path["call_wing_10_pct252"]
                        > float(finalist["call_wing_10_pct252"])
                    )
                ).any()
            )
            if pair_dates:
                status = "paired on close proxy"
            elif breakout_tell:
                status = "unpaired; breakout tell active"
            else:
                status = "unpaired; unresolved"
        elif finalist["scenario"] == "buy-first standard":
            status = "paired on close proxy" if pair_dates else "long unpaired"
        else:
            latest_multiple = float(latest["spread_multiple"])
            if latest_multiple >= 2:
                status = "spread >=2x on close"
            elif latest_multiple >= 1:
                status = "spread above cost"
            else:
                status = "spread below cost"
        outcome_rows.append(
            {
                **finalist.to_dict(),
                "observed_status": status,
                "followup_sessions": len(daily),
                "first_pair_close_date": pair_dates[0] if pair_dates else "",
                "latest_mark_date": latest["tradeDate"],
                "latest_spot": latest["stockPrice"],
                "spot_return_since_signal_pct": (
                    latest["stockPrice"] / float(finalist["stockPrice"]) - 1
                )
                * 100,
                "latest_leg1_bid": latest["leg1_bid"],
                "latest_leg1_ask": latest["leg1_ask"],
                "latest_leg2_bid": latest["leg2_bid"],
                "latest_leg2_ask": latest["leg2_ask"],
                "latest_spread_bid": latest["spread_bid"],
                "latest_mark_pnl_dollars": latest["mark_pnl_dollars"],
                "latest_spread_multiple": latest["spread_multiple"],
                "max_spread_bid": float(daily_frame["spread_bid"].max()),
                "max_spread_multiple": float(daily_frame["spread_multiple"].max()),
                "breakout_tell_active": breakout_tell,
            }
        )

    outcomes = pd.DataFrame(outcome_rows).sort_values(
        ["scenario", "ranking_score"], ascending=[True, False]
    )
    paths = pd.DataFrame(path_rows)
    outcomes.to_csv(output_dir / "single_name_call_screen_outcomes.csv", index=False)
    paths.to_csv(output_dir / "single_name_call_screen_followup_paths.csv", index=False)
    LOG.info(
        "evaluated %d finalists; %d have at least one follow-up close",
        len(outcomes),
        int((outcomes["followup_sessions"] > 0).sum()),
    )


def load_cached_dates(
    cache_dir: Path,
    endpoint: str,
    dates: Iterable[str],
) -> pd.DataFrame:
    """Load and concatenate cached ORATS snapshots."""
    frames: list[pd.DataFrame] = []
    for trade_date in dates:
        path = cache_path(cache_dir, endpoint, trade_date)
        if not path.exists():
            raise FileNotFoundError(f"missing cache file: {path}")
        frames.append(pd.DataFrame(read_gzip_json(path)))
    frame = pd.concat(frames, ignore_index=True)
    frame["tradeDate"] = pd.to_datetime(frame["tradeDate"]).dt.strftime("%Y-%m-%d")
    return frame.drop_duplicates(["tradeDate", "ticker"], keep="last")


def load_cached_history_batches(
    cache_dir: Path,
    endpoint: str,
    dates: Iterable[str],
) -> pd.DataFrame:
    """Load full-history ticker batches and retain the requested sessions."""
    requested_dates = set(dates)
    directory = cache_dir / f"{endpoint.replace('/', '_')}_full"
    frame = load_all_gzip_rows(directory)
    if frame.empty:
        raise FileNotFoundError(f"no full-history cache files below: {directory}")
    frame["tradeDate"] = pd.to_datetime(frame["tradeDate"]).dt.strftime("%Y-%m-%d")
    frame = frame[frame["tradeDate"].isin(requested_dates)].copy()
    if frame.empty:
        raise FileNotFoundError(
            f"full-history cache contains none of the requested sessions: {directory}"
        )
    return frame.drop_duplicates(["tradeDate", "ticker"], keep="last")


def rowwise_prior_percentile(
    values: pd.DataFrame,
    current_date: str,
    *,
    lookback: int = LOOKBACK,
    min_observations: int = MIN_HISTORY,
) -> pd.Series:
    """Calculate causal per-ticker percentiles from a date-by-ticker matrix."""
    location = values.index.get_loc(current_date)
    if not isinstance(location, int):
        raise ValueError(f"ambiguous date index for {current_date}")
    current = values.iloc[location].to_numpy(dtype=float)
    history = values.iloc[max(0, location - lookback) : location].to_numpy(dtype=float)
    valid = np.isfinite(history) & np.isfinite(current)[None, :]
    counts = valid.sum(axis=0)
    below = ((history < current[None, :]) & valid).sum(axis=0)
    percentiles = np.divide(
        below * 100.0,
        counts,
        out=np.full(len(current), np.nan),
        where=counts >= min_observations,
    )
    return pd.Series(percentiles, index=values.columns)


def tier_score(tier: str) -> int:
    """Map buy-first tier labels to an ordinal score."""
    return {"": 0, "good": 1, "better": 2, "best": 3}.get(tier, 0)


def command_analyze(args: argparse.Namespace) -> None:
    """Compute causal signals and write auditable candidate tables."""
    cache_dir = Path(args.cache_dir)
    ticker_universe = (
        read_ticker_universe(Path(args.universe_csv).expanduser())
        if args.universe_csv
        else None
    )
    dailies = read_gzip_json(cache_dir / "hist_dailies" / "SPY_full_history.json.gz")
    all_dates = sorted(
        {
            str(row["tradeDate"])[:10]
            for row in dailies
            if row.get("tradeDate") and str(row["tradeDate"])[:10] <= args.end
        }
    )
    start_index = all_dates.index(args.start)
    end_index = all_dates.index(args.end)
    summary_dates = all_dates[max(0, start_index - LOOKBACK) : end_index + 1]
    target_dates = all_dates[start_index : end_index + 1]

    batch_history_dir = cache_dir / "hist_summaries_full"
    if batch_history_dir.exists() and any(batch_history_dir.glob("*.json.gz")):
        summaries = load_cached_history_batches(
            cache_dir,
            "hist/summaries",
            summary_dates,
        )
    else:
        summaries = load_cached_dates(cache_dir, "hist/summaries", summary_dates)
    numeric(summaries, (*VOL_FIELDS, "stockPrice", "confidence", "mwAdj30"))
    summaries[list(VOL_FIELDS)] *= 100.0  # raw summaries use decimals; rules use vol points
    summaries["rr25"] = (
        summaries["exErnDlt75Iv30d"] - summaries["exErnDlt25Iv30d"]
    )
    summaries["callskew"] = (
        summaries["exErnDlt25Iv30d"] - summaries["exErnIv30d"]
    )
    summaries["call_wing_30"] = summaries["dlt5Iv30d"] - summaries["iv30d"]
    summaries["call_wing_10"] = summaries["dlt5Iv10d"] - summaries["iv10d"]
    summaries["put_wing_10"] = summaries["dlt95Iv10d"] - summaries["iv10d"]
    summaries["call_kink"] = summaries["dlt5Iv10d"] - summaries["dlt5Iv30d"]

    metrics = (
        "rr25",
        "callskew",
        "call_wing_10",
        "put_wing_10",
        "call_kink",
        "iv10d",
    )
    pivots = {
        metric: summaries.pivot(index="tradeDate", columns="ticker", values=metric)
        .sort_index()
        .reindex(summary_dates)
        for metric in metrics
    }
    prices = (
        summaries.pivot(index="tradeDate", columns="ticker", values="stockPrice")
        .sort_index()
        .reindex(summary_dates)
    )

    cores = load_cached_dates(cache_dir, "hist/cores", target_dates)
    numeric(
        cores,
        (
            "priorCls",
            "stkVolu",
            "avgOptVolu20d",
            "oi",
            "mktCap",
            "confidence",
            "mktWidthVol",
            "wksNextErn",
        ),
    )
    ivranks = load_cached_dates(cache_dir, "hist/ivrank", target_dates)
    numeric(ivranks, ("ivRank1y", "ivPct1y", "ivRank1m", "ivPct1m"))

    signal_rows: list[pd.DataFrame] = []
    for trade_date in target_dates:
        current = summaries[summaries["tradeDate"] == trade_date].copy()
        current = current.set_index("ticker")
        for metric, pivot in pivots.items():
            current[f"{metric}_pct252"] = rowwise_prior_percentile(pivot, trade_date)

        location = prices.index.get_loc(trade_date)
        price_now = prices.iloc[location].reindex(current.index)
        price_5d = prices.iloc[max(0, location - 5)].reindex(current.index)
        prior_20 = prices.iloc[max(0, location - 19) : location + 1].reindex(
            columns=current.index
        )
        prior_50 = prices.iloc[max(0, location - 49) : location + 1].reindex(
            columns=current.index
        )
        prior_200 = prices.iloc[max(0, location - 199) : location + 1].reindex(
            columns=current.index
        )
        sma50_20d_ago = prices.iloc[
            max(0, location - 69) : max(0, location - 19)
        ].mean()
        sma50_20d_ago = sma50_20d_ago.reindex(current.index)
        current["return_5d_pct"] = (price_now / price_5d - 1) * 100
        current["drawdown_20d_pct"] = (price_now / prior_20.max() - 1) * 100
        current["sma50"] = prior_50.mean()
        current["sma200"] = prior_200.mean()
        current["extension_50d_pct"] = (price_now / current["sma50"] - 1) * 100
        current["sma50_rising"] = current["sma50"] > sma50_20d_ago
        current["above_200d"] = price_now > current["sma200"]
        current["above_50d"] = price_now > current["sma50"]
        qqq_return_63d = float(
            (price_now.get("QQQ") / prices.iloc[max(0, location - 63)].get("QQQ") - 1)
            * 100
        )
        price_63d = prices.iloc[max(0, location - 63)].reindex(current.index)
        current["return_63d_pct"] = (price_now / price_63d - 1) * 100
        current["relative_return_63d_pct"] = current["return_63d_pct"] - qqq_return_63d

        core_day = cores[cores["tradeDate"] == trade_date].set_index("ticker")
        ivrank_day = ivranks[ivranks["tradeDate"] == trade_date].set_index("ticker")
        joined = current.join(core_day, how="inner", rsuffix="_core").join(
            ivrank_day[["ivRank1y", "ivPct1y", "ivRank1m", "ivPct1m"]],
            how="left",
        )
        if ticker_universe is not None:
            joined = joined[joined.index.isin(ticker_universe)].copy()
        joined["dollar_stock_volume"] = joined["priorCls"] * joined["stkVolu"]
        joined["broad_universe"] = (
            joined.index.to_series().map(is_single_stock_ticker)
            & joined["sectorName"].isin(EQUITY_SECTORS)
            & (joined["avgOptVolu20d"] >= 150)
            & (joined["oi"] >= 1_000)
            & (joined["priorCls"] >= 5)
            & (joined["mktCap"] >= 100_000)
        )
        joined["liquid_final"] = (
            joined["broad_universe"]
            & (joined["avgOptVolu20d"] >= 2_000)
            & (joined["oi"] >= 25_000)
            & (joined["dollar_stock_volume"] >= 20_000_000)
            & (joined["confidence_core"] >= 50)
        )
        broad = joined["broad_universe"]
        joined.loc[broad, "rs63_cross_section_pct"] = joined.loc[
            broad, "relative_return_63d_pct"
        ].rank(pct=True) * 100

        joined["buy_surface_tier"] = joined.apply(
            lambda row: buy_first_tier(
                row["ivRank1y"],
                row["rr25_pct252"],
                row["callskew_pct252"],
                row["call_wing_30"],
                bool(row["iv30d"] < row["iv90d"]),
            ),
            axis=1,
        )
        joined["buy_technical_good"] = (
            joined["above_200d"]
            & (joined["extension_50d_pct"] <= 15)
            & (joined["relative_return_63d_pct"] > 0)
        )
        joined["buy_first_standard"] = (
            joined["buy_surface_tier"].ne("") & joined["buy_technical_good"]
        )
        joined["buy_first_puke"] = (
            (joined["drawdown_20d_pct"] <= -8)
            & (joined["return_5d_pct"] < 0)
            & (joined["rr25_pct252"] >= 60)
            & (joined["callskew_pct252"] <= 40)
            & (joined["ivRank1y"] <= 65)
        )
        joined["sell_archetype"] = joined.apply(
            lambda row: sell_first_archetype(
                row["call_wing_10_pct252"],
                row["call_kink_pct252"],
                row["rr25_pct252"],
                row["put_wing_10_pct252"],
                row["iv10d_pct252"],
                row["return_5d_pct"],
            ),
            axis=1,
        )
        joined["earnings_near_front_expiry"] = joined["wksNextErn"].between(0, 2)
        joined["sell_first_actionable"] = joined.apply(
            lambda row: sell_first_is_actionable(
                row["sell_archetype"],
                row["drawdown_20d_pct"],
                row["ivRank1y"],
                bool(row["earnings_near_front_expiry"]),
            ),
            axis=1,
        )
        joined["buy_score"] = (
            joined["buy_surface_tier"].map(tier_score).fillna(0) * 20
            + joined["buy_first_puke"].astype(int) * 25
            + joined["liquid_final"].astype(int) * 15
            + joined["buy_technical_good"].astype(int) * 10
            + joined["rr25_pct252"].fillna(0) / 10
            - joined["callskew_pct252"].fillna(100) / 20
        )
        joined["sell_score"] = (
            joined["sell_archetype"].map(
                {"": 0, "other": 5, "post-shock smile": 20, "grab": 25}
            ).fillna(0)
            + joined["liquid_final"].astype(int) * 15
            + joined["call_wing_10_pct252"].fillna(0) / 10
            + joined["call_kink_pct252"].fillna(0) / 20
            - joined["earnings_near_front_expiry"].astype(int) * 30
        )
        joined["tradeDate"] = trade_date
        joined["universe_size"] = int(joined["broad_universe"].sum())
        joined["liquid_universe_size"] = int(joined["liquid_final"].sum())
        signal_rows.append(joined.reset_index())
        LOG.info(
            "%s broad=%d liquid=%d buy_standard=%d buy_puke=%d sell_actionable=%d",
            trade_date,
            int(joined["broad_universe"].sum()),
            int(joined["liquid_final"].sum()),
            int((joined["broad_universe"] & joined["buy_first_standard"]).sum()),
            int((joined["broad_universe"] & joined["buy_first_puke"]).sum()),
            int((joined["broad_universe"] & joined["sell_first_actionable"]).sum()),
        )

    all_signals = pd.concat(signal_rows, ignore_index=True)
    all_signals = all_signals[all_signals["broad_universe"]].copy()
    selected = all_signals[
        all_signals["liquid_final"]
        & (
            all_signals["buy_first_standard"]
            | all_signals["buy_first_puke"]
            | all_signals["sell_first_actionable"]
        )
    ].copy()
    selected["scenario"] = np.select(
        [
            selected["sell_first_actionable"],
            selected["buy_first_puke"],
            selected["buy_first_standard"],
        ],
        ["sell-first", "buy-first puke", "buy-first standard"],
        default="",
    )
    selected["ranking_score"] = np.where(
        selected["scenario"].eq("sell-first"),
        selected["sell_score"],
        selected["buy_score"],
    )
    selected = selected.sort_values(
        ["tradeDate", "scenario", "ranking_score"],
        ascending=[True, True, False],
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    columns = [
        "tradeDate",
        "ticker",
        "scenario",
        "buy_surface_tier",
        "sell_archetype",
        "ranking_score",
        "stockPrice",
        "return_5d_pct",
        "drawdown_20d_pct",
        "extension_50d_pct",
        "relative_return_63d_pct",
        "rs63_cross_section_pct",
        "ivRank1y",
        "iv30d",
        "rr25",
        "rr25_pct252",
        "callskew",
        "callskew_pct252",
        "call_wing_30",
        "call_wing_10",
        "call_wing_10_pct252",
        "call_kink",
        "call_kink_pct252",
        "put_wing_10_pct252",
        "iv10d_pct252",
        "avgOptVolu20d",
        "oi",
        "dollar_stock_volume",
        "confidence_core",
        "mktWidthVol",
        "nextErn",
        "wksNextErn",
        "earnings_near_front_expiry",
        "sector",
        "sectorName",
        "bestEtf",
        "universe_size",
        "liquid_universe_size",
    ]
    all_signals.to_parquet(output_dir / "single_name_call_screen_all.parquet", index=False)
    selected[columns].to_csv(
        output_dir / "single_name_call_screen_candidates.csv", index=False
    )
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "start": args.start,
        "end": args.end,
        "dates": target_dates,
        "input_universe_csv": args.universe_csv,
        "input_universe_tickers": len(ticker_universe) if ticker_universe else None,
        "broad_universe_size_by_date": all_signals.groupby("tradeDate")[
            "universe_size"
        ].first().astype(int).to_dict(),
        "liquid_universe_size_by_date": all_signals.groupby("tradeDate")[
            "liquid_universe_size"
        ].first().astype(int).to_dict(),
        "candidate_rows": int(len(selected)),
        "candidate_tickers": int(selected["ticker"].nunique()),
        "scenario_counts": selected["scenario"].value_counts().to_dict(),
        "method": {
            "percentiles": "strict share of prior 252 sessions below current; min 126",
            "broad_universe": (
                "equity sector; avgOptVolu20d>=150; OI>=1,000; price>=5; "
                "market cap>=100m"
            ),
            "liquid_final": (
                "avgOptVolu20d>=2,000; OI>=25,000; stock dollar volume>=20m; "
                "ORATS confidence>=50"
            ),
        },
    }
    (output_dir / "single_name_call_screen_summary.json").write_text(
        json.dumps(summary, indent=2)
    )
    LOG.info(
        "wrote %d candidate rows / %d tickers to %s",
        len(selected),
        selected["ticker"].nunique(),
        output_dir,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE))
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--universe-csv",
        help="optional CSV containing a Ticker column; limits analysis to that set",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="fetch/cache ORATS inputs")
    fetch_parser.add_argument("--max-calls", type=int, default=500)
    fetch_parser.add_argument(
        "--initial-used",
        type=int,
        default=3,
        help="ORATS calls made before this manifest (two probes plus one core snapshot)",
    )
    fetch_parser.add_argument("--rpm", type=int, default=10)
    fetch_parser.add_argument(
        "--env-file",
        default="/Users/dgrissen/Dev/gamma_chaser/.env",
    )
    fetch_parser.set_defaults(function=command_fetch)

    chain_parser = subparsers.add_parser(
        "fetch-chains",
        help="fetch exact historical chains for all surface candidates",
    )
    chain_parser.add_argument("--max-calls", type=int, default=500)
    chain_parser.add_argument("--initial-used", type=int, default=3)
    chain_parser.add_argument("--rpm", type=int, default=10)
    chain_parser.add_argument(
        "--env-file",
        default="/Users/dgrissen/Dev/gamma_chaser/.env",
    )
    chain_parser.set_defaults(function=command_fetch_chains)

    followup_parser = subparsers.add_parser(
        "fetch-followups",
        help="fetch post-signal chains for every exact-chain finalist",
    )
    followup_parser.add_argument("--max-calls", type=int, default=500)
    followup_parser.add_argument("--initial-used", type=int, default=3)
    followup_parser.add_argument("--rpm", type=int, default=10)
    followup_parser.add_argument(
        "--env-file",
        default="/Users/dgrissen/Dev/gamma_chaser/.env",
    )
    followup_parser.set_defaults(function=command_fetch_followups)

    analyze_parser = subparsers.add_parser("analyze", help="compute and rank signals")
    analyze_parser.set_defaults(function=command_analyze)

    confirm_parser = subparsers.add_parser(
        "confirm",
        help="select exact contracts and write chain-confirmed finalists",
    )
    confirm_parser.set_defaults(function=command_confirm)

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="mark finalists on subsequent cached closes",
    )
    evaluate_parser.set_defaults(function=command_evaluate)
    return parser


def main() -> None:
    """Run the selected acquisition or analysis command."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = build_parser().parse_args()
    args.function(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - CLI boundary logs context then preserves failure
        LOG.error("%s: %s", type(error).__name__, error)
        raise
