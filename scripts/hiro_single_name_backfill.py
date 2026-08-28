#!/usr/bin/env python3
"""Backfill ticker-level HIRO after each call-strategy identification date.

The input is the complete surface-qualifier CSV. Each ticker is requested once,
from the calendar day after its first signal through ``--end-date``. The returned
range payload is split into New York market-session partitions before it is
normalized, so cumulative HIRO resets separately for every session. Tickers are
processed serially with a jittered pause and the manifest is updated after each
one, making the run resumable.

The browser is an existing authenticated Chrome leased by the browser-pool
wrapper. This module never activates a page or calls ``bring_to_front``.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import sys
import time
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

import pandas as pd


LOG = logging.getLogger("hiro_single_name_backfill")
HIRO_FINDER_ROOT = Path("/Users/dgrissen/Dev/HIRO_finder")
NEW_YORK = ZoneInfo("America/New_York")
SERIES_GROUPS = ("all", "nextExp", "retail")
MANIFEST_NAME = "manifest.json"
SUMMARY_NAME = "summary.csv"


@dataclass(frozen=True, order=True)
class TickerWindow:
    """One ticker's inclusive historical HIRO request window."""

    ticker: str
    start_date: date
    end_date: date


def build_ticker_windows(candidates: pd.DataFrame, *, end_date: date) -> list[TickerWindow]:
    """Collapse repeated signal rows to each ticker's earliest follow-up window."""
    missing = {"ticker", "tradeDate"} - set(candidates.columns)
    if missing:
        raise ValueError(f"candidate CSV is missing columns: {sorted(missing)}")

    frame = candidates[["ticker", "tradeDate"]].copy()
    frame["ticker"] = frame["ticker"].astype(str).str.strip().str.upper()
    frame["tradeDate"] = pd.to_datetime(frame["tradeDate"], errors="raise").dt.date
    if (frame["ticker"] == "").any():
        raise ValueError("candidate CSV contains an empty ticker")

    windows: list[TickerWindow] = []
    for ticker, rows in frame.groupby("ticker", sort=True):
        first_signal = min(rows["tradeDate"])
        start_date = first_signal + timedelta(days=1)
        if start_date > end_date:
            raise ValueError(
                f"{ticker} first follow-up date {start_date} is after the requested end date"
            )
        windows.append(TickerWindow(ticker, start_date, end_date))
    return windows


def requested_sessions(start_date: date, end_date: date) -> list[date]:
    """Return U.S. market sessions in the inclusive range."""
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    _ensure_hiro_finder_importable()
    from hiro_tickers.orats_dailies import previous_trading_day

    sessions: list[date] = []
    candidate = start_date
    while candidate <= end_date:
        if previous_trading_day(candidate + timedelta(days=1)) == candidate:
            sessions.append(candidate)
        candidate += timedelta(days=1)
    return sessions


def split_payload_by_session(
    payload: Mapping[str, Any],
    *,
    ticker: str,
) -> dict[date, dict[str, dict[str, list[Mapping[str, Any]]]]]:
    """Split a multi-day HIRO response into New York date-specific payloads."""
    symbol = _resolve_payload_symbol(payload, ticker)
    symbol_payload = payload.get(symbol)
    if not isinstance(symbol_payload, Mapping):
        raise ValueError(f"HIRO payload for {ticker} is not an object")

    by_date: dict[date, dict[str, dict[str, list[Mapping[str, Any]]]]] = {}
    for group in SERIES_GROUPS:
        rows = symbol_payload.get(group)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            raw_timestamp = row.get("utc_time")
            try:
                timestamp = float(raw_timestamp)
            except (TypeError, ValueError):
                continue
            session_date = datetime.fromtimestamp(
                timestamp / 1_000,
                tz=timezone.utc,
            ).astimezone(NEW_YORK).date()
            date_payload = by_date.setdefault(
                session_date,
                {ticker: {name: [] for name in SERIES_GROUPS}},
            )
            date_payload[ticker][group].append(row)
    return by_date


def run_backfill(
    *,
    candidate_csv: Path,
    output_root: Path,
    end_date: date,
    port: int,
    pause_min_sec: float,
    pause_max_sec: float,
    retries: int,
    seed: int | None,
    force: bool,
    max_tickers: int | None,
) -> dict[str, Any]:
    """Run a resumable, serial ticker-level HIRO range backfill."""
    if retries < 1:
        raise ValueError("retries must be at least 1")
    if pause_min_sec < 0 or pause_max_sec < pause_min_sec:
        raise ValueError("pause bounds are invalid")
    if not candidate_csv.is_file():
        raise FileNotFoundError(f"candidate CSV does not exist: {candidate_csv}")

    candidates = pd.read_csv(candidate_csv)
    windows = build_ticker_windows(candidates, end_date=end_date)
    if max_tickers is not None:
        windows = windows[: max(0, max_tickers)]
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / MANIFEST_NAME
    manifest = _load_or_initialize_manifest(
        manifest_path,
        candidate_csv=candidate_csv,
        windows=windows,
        end_date=end_date,
        port=port,
    )

    pending = [
        window
        for window in windows
        if force or not _ticker_capture_is_complete(output_root, manifest, window)
    ]
    if not pending:
        manifest["completed"] = True
        _write_manifest_and_summary(manifest, manifest_path)
        return manifest

    _ensure_hiro_finder_importable()
    from hiro_tickers.historical_backfill import fetch_historical_hiro_payload
    from hiro_tickers.live_browser import connect_hiro_browser_session

    browser_session = connect_hiro_browser_session(port=port, navigate=False)
    rng = random.Random(seed)
    try:
        for index, window in enumerate(pending, start=1):
            record = _capture_ticker_range(
                browser_session.page,
                window=window,
                output_root=output_root,
                fetch_fn=fetch_historical_hiro_payload,
                retries=retries,
            )
            manifest["tickers"][window.ticker] = record
            manifest["updated_at_utc"] = _utc_now()
            manifest["completed"] = all(
                _ticker_capture_is_complete(output_root, manifest, item)
                for item in windows
            )
            _write_manifest_and_summary(manifest, manifest_path)
            LOG.info(
                "ticker %d/%d %s status=%s available=%d unavailable=%d rows=%d",
                index,
                len(pending),
                window.ticker,
                record["status"],
                record["available_sessions"],
                record["unavailable_sessions"],
                record["row_count"],
            )
            if index < len(pending):
                delay = rng.uniform(pause_min_sec, pause_max_sec)
                LOG.info("pausing %.1fs before the next ticker", delay)
                time.sleep(delay)
    finally:
        browser_session.close()

    return manifest


def _capture_ticker_range(
    page: Any,
    *,
    window: TickerWindow,
    output_root: Path,
    fetch_fn: Any,
    retries: int,
) -> dict[str, Any]:
    sessions = requested_sessions(window.start_date, window.end_date)
    last_error: str | None = None
    payload: Mapping[str, Any] | None = None
    for attempt in range(1, retries + 1):
        try:
            payload = fetch_fn(
                page,
                symbol=window.ticker,
                start_date=window.start_date.isoformat(),
                end_date=window.end_date.isoformat(),
                timeout_ms=90_000,
            )
            break
        except Exception as exc:  # noqa: BLE001 - record failure and continue the batch
            last_error = f"{type(exc).__name__}: {exc}"
            LOG.warning(
                "%s range request failed attempt=%d/%d: %s",
                window.ticker,
                attempt,
                retries,
                last_error,
            )
            if attempt < retries:
                time.sleep(2**attempt)

    if payload is None:
        return _failure_record(window, sessions=sessions, error=last_error or "unknown error")

    split = split_payload_by_session(payload, ticker=window.ticker)
    available = 0
    unavailable = 0
    row_count = 0
    session_records: dict[str, Any] = {}
    for session_date in sessions:
        date_payload = split.get(
            session_date,
            {window.ticker: {name: [] for name in SERIES_GROUPS}},
        )
        record = _write_session_partition(
            output_root,
            ticker=window.ticker,
            session_date=session_date,
            payload=date_payload,
        )
        session_records[session_date.isoformat()] = record
        row_count += int(record["row_count"])
        if record["status"] == "success":
            available += 1
        else:
            unavailable += 1

    return {
        "ticker": window.ticker,
        "start_date": window.start_date.isoformat(),
        "end_date": window.end_date.isoformat(),
        "status": "success",
        "available_sessions": available,
        "unavailable_sessions": unavailable,
        "row_count": row_count,
        "error": None,
        "captured_at_utc": _utc_now(),
        "sessions": session_records,
    }


def _write_session_partition(
    output_root: Path,
    *,
    ticker: str,
    session_date: date,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    _ensure_hiro_finder_importable()
    from hiro_tickers.live_monitor import safe_ticker, write_normalized_series_csv

    partition = output_root / f"ticker={safe_ticker(ticker)}" / f"date={session_date}"
    raw_path = partition / "raw" / "v11_hiro.json"
    series_path = partition / "normalized" / "hiro_series.csv"
    _write_json_atomic(raw_path, payload)
    temporary_series = series_path.with_suffix(".csv.tmp")
    write_normalized_series_csv(payload, ticker=ticker, path=temporary_series)
    temporary_series.replace(series_path)

    symbol_payload = payload.get(ticker, {})
    row_count = sum(
        len(rows)
        for group in SERIES_GROUPS
        if isinstance(symbol_payload, Mapping)
        and isinstance((rows := symbol_payload.get(group)), list)
    )
    return {
        "status": "success" if row_count else "unavailable",
        "row_count": row_count,
        "raw_json": str(raw_path),
        "series_csv": str(series_path),
    }


def _failure_record(
    window: TickerWindow,
    *,
    sessions: Sequence[date],
    error: str,
) -> dict[str, Any]:
    return {
        "ticker": window.ticker,
        "start_date": window.start_date.isoformat(),
        "end_date": window.end_date.isoformat(),
        "status": "failed",
        "available_sessions": 0,
        "unavailable_sessions": 0,
        "row_count": 0,
        "error": error,
        "captured_at_utc": _utc_now(),
        "sessions": {value.isoformat(): {"status": "failed"} for value in sessions},
    }


def _ticker_capture_is_complete(
    output_root: Path,
    manifest: Mapping[str, Any],
    window: TickerWindow,
) -> bool:
    record = manifest.get("tickers", {}).get(window.ticker, {})
    if record.get("status") != "success":
        return False
    for session_date in requested_sessions(window.start_date, window.end_date):
        session = record.get("sessions", {}).get(session_date.isoformat(), {})
        raw_path = session.get("raw_json")
        series_path = session.get("series_csv")
        if session.get("status") not in {"success", "unavailable"}:
            return False
        if not raw_path or not Path(raw_path).is_file():
            return False
        if not series_path or not Path(series_path).is_file():
            return False
    return True


def _load_or_initialize_manifest(
    path: Path,
    *,
    candidate_csv: Path,
    windows: Sequence[TickerWindow],
    end_date: date,
    port: int,
) -> dict[str, Any]:
    candidate_hash = hashlib.sha256(candidate_csv.read_bytes()).hexdigest()
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("candidate_sha256") != candidate_hash:
            raise ValueError(
                "candidate CSV changed since this output manifest was created; "
                "use a new output directory"
            )
        return existing
    return {
        "schema_version": 1,
        "purpose": "Ticker-level HIRO follow-through after call-strategy identification.",
        "created_at_utc": _utc_now(),
        "updated_at_utc": _utc_now(),
        "candidate_csv": str(candidate_csv),
        "candidate_sha256": candidate_hash,
        "end_date": end_date.isoformat(),
        "browser_port": port,
        "ticker_count": len(windows),
        "capture_scope": (
            "All/Next Expiry/Retail provider rows; New York session partitions; "
            "the end-date session may be partial at capture time."
        ),
        "completed": False,
        "tickers": {},
    }


def _write_manifest_and_summary(manifest: Mapping[str, Any], path: Path) -> None:
    _write_json_atomic(path, manifest)
    summary_path = path.parent / SUMMARY_NAME
    temporary = summary_path.with_suffix(".csv.tmp")
    fields = (
        "ticker",
        "start_date",
        "end_date",
        "status",
        "available_sessions",
        "unavailable_sessions",
        "row_count",
        "error",
        "captured_at_utc",
    )
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for ticker in sorted(manifest.get("tickers", {})):
            record = manifest["tickers"][ticker]
            writer.writerow({field: record.get(field) for field in fields})
    temporary.replace(summary_path)


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _resolve_payload_symbol(payload: Mapping[str, Any], ticker: str) -> str:
    target = ticker.strip().upper()
    for key in payload:
        if str(key).strip().upper() == target:
            return str(key)
    if len(payload) == 1:
        return str(next(iter(payload)))
    raise ValueError(f"could not find {ticker!r} in HIRO payload keys")


def _ensure_hiro_finder_importable() -> None:
    root = str(HIRO_FINDER_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("BROWSER_CDP_PORT", "9222")),
    )
    parser.add_argument("--pause-min-sec", type=float, default=6.0)
    parser.add_argument("--pause-max-sec", type=float, default=12.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-tickers", type=int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    manifest = run_backfill(
        candidate_csv=Path(args.candidate_csv).expanduser().resolve(),
        output_root=Path(args.out_dir).expanduser().resolve(),
        end_date=date.fromisoformat(args.end_date),
        port=args.port,
        pause_min_sec=args.pause_min_sec,
        pause_max_sec=args.pause_max_sec,
        retries=args.retries,
        seed=args.seed,
        force=args.force,
        max_tickers=args.max_tickers,
    )
    print(f"Manifest: {Path(args.out_dir).expanduser().resolve() / MANIFEST_NAME}")
    return 0 if manifest.get("completed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
