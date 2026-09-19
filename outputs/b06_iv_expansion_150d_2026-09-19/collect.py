"""Collect a frozen 100-day extension using native ThetaData SDK observations."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import contextlib
from datetime import date
import hashlib
import importlib.util
import io
import json
import logging
from pathlib import Path
import threading
import time
from typing import Any

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
OLD = OUT.parent / "b06_sector_surface_50d_2026-09-13"
CENTRAL = Path("/Users/dgrissen/Dev/central_trade_data/thetadata")
DATA = CENTRAL / "b06_iv_expansion_150d_2026-09-19-v1"
SYMBOLS = ["XLC", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI", "XLB", "XLRE", "XLK", "XLU"]
START, END = date(2025, 1, 1), date(2026, 9, 18)


def module(name: str, filename: str) -> Any:
    """Load a specific read-only source module without invoking its main."""
    spec = importlib.util.spec_from_file_location(name, OLD / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


sampler = module("frozen_sampling", "sample_days.py")
normalizer = module("frozen_normalizer", "fetch_spx_coverage.py")
legacy = module("frozen_collector", "download.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(phase: str, **values: Any) -> None:
    print(json.dumps({"phase": phase, **values}, default=str), flush=True)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    pending.replace(path)


def freeze_json(path: Path, value: Any) -> None:
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError(f"Frozen artifact differs: {path}")
    else:
        write_json(path, value)


def request_key(method: str, params: dict[str, Any]) -> str:
    safe = json.loads(json.dumps(params, default=str))
    return hashlib.sha256(json.dumps([method, safe], sort_keys=True).encode()).hexdigest()


def select_expiries(day: date, expirations: list[date]) -> list[date]:
    return legacy.expiries(day, expirations)


def load_levels(path: Path) -> list[dict[str, Any]]:
    """Keep every dated VT record in the fixed two-year window."""
    frame = pd.read_csv(path)
    days = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="raise").dt.date
    frame = frame.loc[days.between(START, END)].copy()
    if frame.Date.duplicated().any():
        raise ValueError("Duplicate VT dates")
    rows = []
    for index, row in frame.iterrows():
        value = pd.to_numeric(row["Vol Trigger"], errors="coerce")
        rows.append({"date": row["Date"], "vol_trigger": float(value) if np.isfinite(value)
                     else None, "vt_csv_line": int(index) + 2})
    return sorted(rows, key=lambda r: r["date"])


def exclude_prior_days(ledger: pd.DataFrame, prior: set[str]) -> pd.DataFrame:
    result = ledger.copy()
    mask = result.date.isin(prior)
    result.loc[mask, "eligible"] = False
    result.loc[mask, "exclusion_reasons"] = result.loc[mask, "exclusion_reasons"].map(
        lambda reason: "|".join(x for x in [reason, "original_fifty_day"] if x))
    result["original_fifty_day"] = mask
    return result


_original_spx_source = sampler._spx_source


def locate_spx(day: str, old: Path, new: Path,
               hashes: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source, attempts = _original_spx_source(day, old, new, hashes)
    if source["complete"]:
        return source, attempts
    extra, extra_attempts = _original_spx_source(
        day, DATA / "spx_normalized", DATA / "no_fallback", hashes)
    return (extra if extra["complete"] else source), attempts + extra_attempts[:1]


def population() -> tuple[pd.DataFrame, dict[str, Any], dict[str, str]]:
    sampler._load_levels = load_levels
    sampler._spx_source = locate_spx
    sampler.AS_OF = END
    ledger, provenance, hashes = sampler.build_population(
        sampler.DEFAULT_VT, sampler.DEFAULT_ORIGINAL, sampler.DEFAULT_NEW,
        sampler.DEFAULT_NOTES, sampler.DEFAULT_MANIFEST)
    prior_path = OLD / "selected_days.csv"
    prior = set(pd.read_csv(prior_path).date)
    if len(prior) != 50:
        raise ValueError("Original sample is not fifty unique days")
    hashes[str(prior_path)] = digest(prior_path)
    for source in [Path(__file__), OUT / "PROTOCOL.md", OLD / "sample_days.py",
                   OLD / "fetch_spx_coverage.py", OLD / "download.py"]:
        hashes[str(source)] = digest(source)
    return exclude_prior_days(ledger, prior), provenance, hashes


def authenticate() -> Any:
    """Use existing account credentials without exposing SDK auth output."""
    from thetadata import ThetaClient
    logging.getLogger("thetadata").setLevel(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            client = ThetaClient(creds_file="/Users/dgrissen/Dev/ThetaData/creds.txt",
                                 dataframe_type="pandas")
    except Exception as exc:
        raise RuntimeError(f"Theta authentication failed: {type(exc).__name__}") from None
    emit("authenticated")
    return client


class SDKCache:
    """Use immutable raw cache and at most one logged retry per transient request."""

    def __init__(self, client: Any) -> None:
        self.client = client
        self.cache = legacy.Cache(DATA, limit=10000)
        self.lock = threading.Lock()
        self.attempts: dict[str, int] = {}
        for line in self.cache.log.read_text().splitlines() if self.cache.log.exists() else []:
            row = json.loads(line)
            if row["status"] == "started":
                key = row["key"]
                self.attempts[key] = self.attempts.get(key, 0) + 1

    def get(self, method: str, params: dict[str, Any]) -> tuple[pd.DataFrame, Path]:
        key = request_key(method, params)
        safe = json.loads(json.dumps(params, default=str))
        meta_path = DATA / method / (key + ".json")
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            if meta["method"] != method or meta["params"] != safe:
                raise ValueError("Cached request parameters differ")
            return self.cache.get(method, params, getattr(self.client, method))
        # Reuse exact matching prior-cache inputs read-only; never trust just a filename.
        for existing in sorted(CENTRAL.glob("*/" + method + "/" + key + ".json")):
            if DATA in existing.parents:
                continue
            meta = json.loads(existing.read_text())
            raw = existing.with_suffix(".parquet")
            if (meta.get("method") == method and meta.get("params") == safe
                    and raw.exists() and digest(raw) == meta["sha256"]):
                with self.lock:
                    self.cache.record({"status": "reused_external", "method": method,
                                       "key": key, "path": str(raw), "sha256": meta["sha256"]})
                return pd.read_parquet(raw), raw
        while True:
            with self.lock:
                count = self.attempts.get(key, 0)
                if count >= 2:
                    raise RuntimeError("Recorded request attempt ceiling reached")
                self.attempts[key] = count + 1
            try:
                return self.cache.get(method, params, getattr(self.client, method))
            except RuntimeError as exc:
                message = str(exc)
                transient = any(token in message.upper() for token in [
                    "DEADLINE_EXCEEDED", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
                    "TIMEOUT", "INTERNAL", "TOO_MANY_REQUESTS"])
                if not transient or count >= 1:
                    raise
                with self.lock:
                    self.cache.record({"status": "retry_authorized_transient", "key": key,
                                       "method": method, "attempt": count + 2})
                time.sleep(1)


def audit_and_sample() -> None:
    """Complete the full sampling universe before one immutable random draw."""
    if (OUT / "sampling_manifest.json").exists():
        manifest = json.loads((OUT / "sampling_manifest.json").read_text())
        for path, expected in manifest["source_hashes"].items():
            if digest(Path(path)) != expected:
                raise ValueError(f"Frozen sampling source changed: {path}")
        emit("sample_already_frozen", count=manifest["sample_count"])
        return
    ledger, _, _ = population()
    ledger.to_csv(OUT / "population_pre_coverage.csv", index=False)
    needed = ledger.loc[~ledger.complete_spx & ledger.vol_trigger.gt(0), "date"].tolist()
    if len(needed) > 500:
        raise ValueError("SPX collection exceeds protocol maximum")
    emit("coverage_plan", dated_records=len(ledger), fetch_dates=len(needed),
         currently_eligible=int(ledger.eligible.sum()))
    results = []
    if needed:
        cache = SDKCache(authenticate())

        def collect_spx(day: str) -> dict[str, Any]:
            try:
                raw, path = cache.get("index_history_ohlc", normalizer.request_params(
                    date.fromisoformat(day)))
                frame, info = normalizer.normalize_native(raw, date.fromisoformat(day))
                output = DATA / "spx_normalized" / (day + ".parquet")
                output.parent.mkdir(parents=True, exist_ok=True)
                if output.exists():
                    prior = pd.read_parquet(output)
                    pd.testing.assert_frame_equal(frame, prior)
                else:
                    frame.to_parquet(output, index=False)
                record = {"date": day, "status": "ok", "raw_path": str(path),
                          "raw_sha256": digest(path), "path": str(output),
                          "sha256": digest(output), **info}
                freeze_json(output.with_suffix(".json"), record)
                return record
            except (RuntimeError, ValueError) as exc:
                return {"date": day, "status": "error", "error": str(exc)}
        with ThreadPoolExecutor(max_workers=2) as pool:
            tasks = [pool.submit(collect_spx, day) for day in needed]
            for future in as_completed(tasks):
                result = future.result()
                results.append(result)
                emit("spx", completed=len(results), total=len(needed),
                     date=result["date"], status=result["status"],
                     complete=result.get("complete", False))
    write_json(OUT / "spx_coverage_download.json",
               {"status": "complete", "requested_dates": needed, "records": results})
    ledger, provenance, hashes = population()
    hashes[str(OUT / "spx_coverage_download.json")] = digest(OUT / "spx_coverage_download.json")
    selected = sampler.freeze_sample(ledger, provenance, hashes, OUT, count=100)
    emit("sample_frozen", eligible=int(ledger.eligible.sum()), count=len(selected),
         selected_years=selected.date.str[:4].value_counts().to_dict(),
         excluded=ledger.loc[~ledger.eligible, "exclusion_reasons"].value_counts().to_dict())


def options() -> None:
    """Fetch only the already sampled dates, keeping all coverage failures."""
    selected = pd.read_csv(OUT / "selected_days.csv")
    dates = selected.date.tolist()
    if len(dates) != 100 or len(set(dates)) != 100:
        raise ValueError("Need exactly 100 distinct frozen extension dates")
    frozen = json.loads((OUT / "sampling_manifest.json").read_text())
    if dates != frozen["selected_dates"]:
        raise ValueError("Sample differs from frozen draw")
    freeze_json(DATA / "sampling_freeze.json",
                {"path": str(OUT / "selected_days.csv"),
                 "sha256": digest(OUT / "selected_days.csv")})
    protocol = {"path": str(OUT / "PROTOCOL.md"), "sha256": digest(OUT / "PROTOCOL.md")}
    freeze_json(DATA / "protocol_freeze.json", protocol)
    cache = SDKCache(authenticate())
    selections, listing_sources = [], []
    for day_string in dates:
        day = date.fromisoformat(day_string)
        try:
            listing, path = cache.get("option_list_contracts",
                {"request_type": "quote", "date": day, "symbol": SYMBOLS, "max_dte": 65})
            listing_sources.append({"date": day_string, "path": str(path), "sha256": digest(path)})
            for symbol in SYMBOLS:
                values = pd.to_datetime(listing.loc[listing.symbol.eq(symbol), "expiration"]
                                        ).dt.date.tolist()
                expirations = select_expiries(day, values)
                selections.append({"date": day_string, "symbol": symbol,
                    "expirations": [str(e) for e in expirations],
                    "status": "selected" if expirations else "missing_tenor_bracket"})
            emit("listing", date=day_string, rows=len(listing),
                 completed=len(listing_sources), total=100)
        except RuntimeError as exc:
            listing_sources.append({"date": day_string, "status": "error", "error": str(exc)})
            selections.extend({"date": day_string, "symbol": symbol, "expirations": [],
                               "status": "listing_error"} for symbol in SYMBOLS)
            emit("listing_error", date=day_string, error=str(exc))
    freeze_json(DATA / "selections.json",
                {"sources": listing_sources, "selections": selections})
    tasks = [(s["date"], s["symbol"], exp) for s in selections for exp in s["expirations"]]
    if len(tasks) * 2 + len(dates) > 4500:
        raise ValueError("Option collection exceeds base protocol ceiling")
    emit("option_plan", expiry_pairs=len(tasks), base_calls=2 * len(tasks) + len(dates))
    records: list[dict[str, Any]] = []
    manifest = {"protocol": protocol, "dates": dates, "symbols": SYMBOLS,
                "selections": selections, "listing_sources": listing_sources,
                "planned_pairs": len(tasks), "pairs": records, "status": "collecting"}

    def checkpoint() -> None:
        manifest["at"] = legacy.now()
        write_json(DATA / "manifest.json", manifest)
        write_json(OUT / "collection_manifest.json", manifest)

    def collect_pair(task: tuple[str, str, str]) -> dict[str, Any]:
        day, symbol, expiry = task
        params = {"symbol": symbol, "expiration": date.fromisoformat(expiry),
                  "date": date.fromisoformat(day), "interval": "1m", "strike": "*",
                  "right": "both", "start_time": "09:30:00", "end_time": "14:29:00",
                  "strike_range": 30, "rate_type": "sofr", "version": "latest"}
        record: dict[str, Any] = {"date": day, "symbol": symbol, "expiration": expiry, "files": []}
        for kind in ["implied_volatility", "first_order"]:
            try:
                frame, path = cache.get("option_history_greeks_" + kind, params)
                if len(frame) and (not frame.symbol.eq(symbol).all()
                    or not pd.to_datetime(frame.expiration).dt.date.eq(date.fromisoformat(expiry)).all()):
                    raise ValueError("Response contract mismatch")
                record["files"].append({"kind": kind, "path": str(path), "rows": len(frame),
                                        "sha256": digest(path)})
            except (RuntimeError, ValueError) as exc:
                return record | {"status": "error", "error": str(exc)}
        return record | {"status": "ok"}

    checkpoint()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(collect_pair, task) for task in tasks]
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            checkpoint()
            if len(records) % 10 == 0 or record["status"] != "ok" or len(records) == len(tasks):
                emit("option_history", completed=len(records), total=len(tasks),
                     date=record["date"], symbol=record["symbol"], status=record["status"])
    manifest["status"] = ("complete" if all(r["status"] == "ok" for r in records)
                          and all("error" not in r for r in listing_sources)
                          else "complete_with_errors")
    checkpoint()
    emit("collection_complete", status=manifest["status"],
         pairs=len(records), failed=sum(r["status"] != "ok" for r in records))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["sample", "options"])
    args = parser.parse_args()
    {"sample": audit_and_sample, "options": options}[args.stage]()
