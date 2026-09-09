"""Batched, cached data acquisition under the user's shared 2,000-attempt ceiling."""

from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import os
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/pandar_hypothesis_2026-09-07"
BUDGET_PATH = ROOT / "outputs/pandar_hypothesis_2026-09-07/api_budget.json"


class BudgetExceeded(RuntimeError):
    """The preauthorized program budget has been consumed."""


class SharedBudget:
    """Serialize reservations across threads/processes before every provider attempt."""

    def __init__(self, path: Path = BUDGET_PATH, limit: int = 2000) -> None:
        self.path, self.limit = path, limit
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._locked() as data:
            if data["limit"] != limit:
                raise ValueError("existing budget limit differs")

    @contextmanager
    def _locked(self) -> Iterator[dict[str, Any]]:
        with self.path.with_suffix(".lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text()) if self.path.exists() else {
                "limit": self.limit, "used": 0, "attempts": [],
                "authorization": "User authorized up to 2000 calls; all program providers share cap",
            }
            yield data
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, indent=2) + "\n")
            temporary.replace(self.path)

    def reserve(self, provider: str, endpoint: str, params: dict[str, Any], phase: str) -> int:
        """Reserve once before I/O; a failed request still consumes its reservation."""
        if any(any(s in key.lower() for s in ("token", "secret", "password", "api_key"))
               for key in params):
            raise ValueError("secret parameter cannot enter budget ledger")
        with self._locked() as data:
            if data["used"] >= data["limit"]:
                raise BudgetExceeded(f"program ceiling reached: {data['used']}")
            data["used"] += 1
            attempt_id = data["used"]
            data["attempts"].append({
                "id": attempt_id, "provider": provider, "endpoint": endpoint,
                "params": params, "phase": phase, "status": "started",
                "at": datetime.now(UTC).isoformat(),
            })
        return attempt_id

    def finish(self, attempt_id: int, status: str, **safe_fields: Any) -> None:
        """Record a safe status without logging URLs, headers or exception strings."""
        with self._locked() as data:
            item = next(item for item in data["attempts"] if item["id"] == attempt_id)
            item.update(status=status, **safe_fields)


def ticker_batches(tickers: list[str]) -> Iterator[list[str]]:
    """Yield unique symbols in deterministic groups of at most ten."""
    values = sorted(set(tickers))
    for offset in range(0, len(values), 10):
        yield values[offset:offset + 10]


class Orats:
    """Secret-safe cache client; caller supplies endpoint phase for auditability."""

    def __init__(self, budget: SharedBudget | None = None) -> None:
        load_dotenv("/Users/dgrissen/Dev/gamma_chaser/.env")
        self.token = os.environ.get("ORATS_API_KEY", "")
        if not self.token:
            raise RuntimeError("ORATS_API_KEY unavailable")
        self.budget = budget or SharedBudget()
        self.session = requests.Session()
        self.session.headers.update({"Accept-Encoding": "gzip"})

    def get(self, endpoint: str, params: dict[str, str], phase: str,
            attempts: int = 2) -> list[dict[str, Any]]:
        """Fetch one bounded batch, caching successes and counting each retry."""
        tickers = params.get("ticker", "").split(",")
        if len(tickers) > 10 or ("one-minute" in endpoint and len(tickers) > 1):
            raise ValueError("endpoint ticker batch exceeds supported limit")
        denial = DATA / "denied_endpoints.json"
        denied = json.loads(denial.read_text()) if denial.exists() else {}
        if endpoint in denied:
            raise RuntimeError(f"ORATS endpoint denied earlier; no new call: {endpoint}")
        key = hashlib.sha256(json.dumps([endpoint, params], sort_keys=True).encode()).hexdigest()
        path = DATA / "raw" / endpoint.replace("/", "_") / f"{key}.json.gz"
        if path.exists():
            with gzip.open(path, "rt") as handle:
                return json.load(handle)["data"]
        for attempt in range(attempts):
            number = self.budget.reserve("orats", endpoint, params, phase)
            try:
                response = self.session.get(
                    f"https://api.orats.io/datav2/{endpoint}",
                    params={**params, "token": self.token}, timeout=(20, 180),
                )
            except requests.RequestException:
                self.budget.finish(number, "connection_failure")
                if attempt + 1 == attempts:
                    raise RuntimeError(f"ORATS connection failure: {endpoint}") from None
                time.sleep(2)
                continue
            if response.status_code != 200:
                self.budget.finish(number, "http_error", http_status=response.status_code)
                if response.status_code in {401, 403} and "one-minute" in endpoint:
                    denied[endpoint] = {"http_status": response.status_code, "attempt_id": number}
                    denial.parent.mkdir(parents=True, exist_ok=True)
                    denial.write_text(json.dumps(denied, indent=2) + "\n")
                if response.status_code in {429, 500, 502, 503, 504} and attempt + 1 < attempts:
                    time.sleep(3)
                    continue
                raise RuntimeError(f"ORATS HTTP {response.status_code}: {endpoint}")
            try:
                rows = response.json()["data"]
                if not isinstance(rows, list):
                    raise ValueError("data is not a list")
            except (ValueError, KeyError):
                self.budget.finish(number, "invalid_payload")
                raise RuntimeError(f"Invalid ORATS payload: {endpoint}") from None
            path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(path, "wt") as handle:
                json.dump({"retrieved_at": datetime.now(UTC).isoformat(), "endpoint": endpoint,
                           "params": params, "data": rows}, handle)
            self.budget.finish(number, "ok", rows=len(rows), cache_path=str(path),
                               sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            return rows
        raise AssertionError("unreachable")

    def batched(self, endpoint: str, tickers: list[str], params: dict[str, str],
                phase: str) -> list[dict[str, Any]]:
        """Auto-chunk requests internally; no endpoint receives more than ten symbols."""
        rows = []
        for batch in ticker_batches(tickers):
            rows.extend(self.get(endpoint, {**params, "ticker": ",".join(batch)}, phase))
        return rows


def refresh_metadata(probe: bool = False) -> None:
    """Refresh actual earnings and split history for the frozen HIRO stock membership."""
    universe = pd.read_csv(ROOT / "docs/replay/pandar_skew_journey_2026-09-06/hiro_universe.csv")
    stocks = universe.loc[universe["single_stock"].eq(True), "ticker"].tolist()
    if probe:
        stocks = stocks[:10]
    client = Orats()
    DATA.mkdir(parents=True, exist_ok=True)
    coverage = {ticker: {"ticker": ticker} for ticker in stocks}
    for label, endpoint, date_field in (("earnings", "hist/earnings", "earnDate"),
                                       ("splits", "hist/splits", "splitDate")):
        collected = []
        # Live probe: splits silently returns [] for comma-delimited symbols.
        # Unlike earnings, its batching claim in the skill is not supported here.
        if label == "splits" and not probe:
            readiness = json.loads((ROOT / "outputs/pandar_hypothesis_2026-09-07/data_readiness.json").read_text())
            needed = {row["ticker"] for row in readiness["high_skew_next_session_pairs"]
                      if "2024-01-02" <= row["tradeDate"] <= "2026-08-05"}
            for ticker in stocks:
                coverage[ticker]["splits_status"] = "not_requested_no_eligible_hiro_signal"
            batches = [[ticker] for ticker in sorted(needed)]
        else:
            batches = [[ticker] for ticker in stocks] if label == "splits" else ticker_batches(stocks)
        for batch in batches:
            try:
                rows = client.get(endpoint, {"ticker": ",".join(batch)}, "metadata")
            except RuntimeError as exc:
                print(json.dumps({"endpoint": endpoint, "tickers": batch,
                                  "status": str(exc)}), flush=True)
                for ticker in batch:
                    coverage[ticker][f"{label}_status"] = "failed"
                continue
            collected.extend(rows)
            for ticker in batch:
                relevant = [row for row in rows if row.get("ticker") == ticker]
                dated = pd.to_datetime([row.get(date_field) for row in relevant], errors="coerce")
                valid = dated[~dated.isna()]
                supported = len(valid) > 0 if label == "earnings" else True
                coverage[ticker].update({
                    f"{label}_status": "ok" if supported else "missing_events",
                    f"{label}_coverage_start": str(valid.min().date()) if label == "earnings" and len(valid) else "1900-01-01",
                    f"{label}_coverage_end": "2026-09-04",
                    f"{label}_rows": len(relevant),
                })
            print(json.dumps({"endpoint": endpoint, "batch": batch, "rows": len(rows)}), flush=True)
        suffix = "_probe" if probe else ""
        normalized = pd.DataFrame(collected)
        if date_field in normalized:
            valid_dates = pd.to_datetime(normalized[date_field], errors="coerce").notna()
            normalized.loc[~valid_dates].to_parquet(DATA / f"{label}{suffix}_invalid_dates.parquet",
                                                  index=False)
            normalized = normalized.loc[valid_dates].copy()
        normalized.to_parquet(DATA / f"{label}{suffix}.parquet", index=False)
    pd.DataFrame(coverage.values()).to_csv(DATA / f"metadata_coverage{'_probe' if probe else ''}.csv",
                                         index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", action="store_true")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if args.metadata:
        refresh_metadata(args.probe)
