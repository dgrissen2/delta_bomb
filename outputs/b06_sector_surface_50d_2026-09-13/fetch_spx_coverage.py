"""Fill native SPX coverage for the frozen 2026 VT sampling universe, before outcomes.

The old native cache is read-only. Every requested SDK response is retained unchanged
through the existing immutable raw Cache. Normalized files preserve native observations;
partial sessions remain partial and no prices, minutes or timestamps are synthesized.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import contextlib
from datetime import date, datetime, timezone
import hashlib
import importlib.util
import io
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


OUT = Path(__file__).resolve().parent
DATA = Path(
    "/Users/dgrissen/Dev/central_trade_data/thetadata/sector_surface_b06_50d_2026-09-13-v1"
)
VT_SOURCE = Path(
    "/Users/dgrissen/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv"
)
NATIVE_ROOT = Path("/Users/dgrissen/Dev/central_trade_data/thetadata/spx_index_1m_ohlc")
LEGACY_DOWNLOAD = (
    OUT.parent / "branch_b_above_vt_10d_2026-09-12"
    / "sector_surface_breadth_2026-09-13" / "download.py"
)
START, END = date(2026, 1, 2), date(2026, 9, 11)
MAX_REQUESTS = 40
ET = "America/New_York"
OHLC = ["open", "high", "low", "close"]
EXPECTED_MINUTES = list(range(570, 960))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_ohlc(frame: pd.DataFrame) -> pd.DataFrame:
    if missing := set(OHLC).difference(frame.columns):
        raise ValueError(f"Missing OHLC columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Empty native OHLC response")
    numeric = frame[OHLC].apply(pd.to_numeric, errors="coerce")
    valid = (np.isfinite(numeric) & numeric.gt(0)).all(axis=1)
    valid &= numeric.high.ge(numeric[["open", "close", "low"]].max(axis=1))
    valid &= numeric.low.le(numeric[["open", "close", "high"]].min(axis=1))
    if not valid.all():
        raise ValueError(f"Invalid OHLC observations: {int((~valid).sum())}")
    result = frame.copy()
    result[OHLC] = numeric
    return result


def _minute_coverage(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    if "min" not in frame:
        raise ValueError("Missing native minute column")
    minutes = pd.to_numeric(frame["min"], errors="coerce")
    if not (np.isfinite(minutes) & minutes.eq(minutes.round()) & minutes.between(570, 960)).all():
        raise ValueError("Native minutes must be integers from 09:30 through 16:00")
    if minutes.duplicated().any():
        raise ValueError("Duplicate native start minute")
    result = frame.copy()
    result["min"] = minutes.astype("int32")
    excluded = int(result["min"].eq(960).sum())
    result = result[result["min"].lt(960)].sort_values("min").reset_index(drop=True)
    observed = set(result["min"].tolist())
    missing = sorted(set(EXPECTED_MINUTES) - observed)
    return result, {
        "valid": True, "complete": not missing and len(result) == 390,
        "raw_rows": len(frame), "rth_rows": len(result), "expected_rth_rows": 390,
        "missing_minutes": missing, "excluded_1600_rows": excluded,
        "filled_minutes": 0,
    }


def normalize_native(raw: pd.DataFrame, day: date) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate native timestamps/OHLC and retain only observed 09:30–15:59 ET bars.

    A valid partial day is returned with complete=False and its missing minute list.
    Timestamp ambiguity, duplicate observations, wrong dates and invalid OHLC raise
    ValueError; the caller preserves the raw response and records that rejection.
    """
    if "timestamp" not in raw:
        raise ValueError("Missing native timestamp column")
    source_times = raw.timestamp
    if isinstance(source_times.dtype, pd.DatetimeTZDtype):
        timestamps = source_times.dt.tz_convert(ET)
        if timestamps.isna().any():
            raise ValueError("Native timestamps must be valid and timezone-aware")
    else:
        parsed = [pd.Timestamp(value) for value in source_times]
        if any(pd.isna(value) or value.tzinfo is None for value in parsed):
            raise ValueError("Native timestamps must be valid and timezone-aware")
        timestamps = pd.Series(pd.to_datetime(parsed, utc=True).tz_convert(ET), index=raw.index)
    if not timestamps.dt.date.eq(day).all():
        raise ValueError("Native timestamp ET date differs from the requested session")
    if not timestamps.eq(timestamps.dt.floor("min")).all():
        raise ValueError("Native timestamps must identify exact start minutes")
    if timestamps.duplicated().any():
        raise ValueError("Duplicate native start minute")
    if "symbol" in raw and not raw.symbol.eq("SPX").all():
        raise ValueError("Native symbol differs from requested SPX")
    normalized = _validate_ohlc(raw)
    normalized["timestamp"] = timestamps
    minutes = timestamps.dt.hour * 60 + timestamps.dt.minute
    if "min" in raw and not pd.to_numeric(raw["min"], errors="coerce").eq(minutes).all():
        raise ValueError("Native minute column disagrees with the source timestamp")
    normalized["min"] = minutes
    normalized, info = _minute_coverage(normalized)
    info.update(date=day.isoformat(), timezone=ET, source_timestamp_column="timestamp")
    return normalized, info


def _existing(path: Path, day: str) -> dict[str, Any]:
    record: dict[str, Any] = {"date": day, "path": str(path), "complete": False}
    if not path.exists():
        return record | {"status": "missing"}
    record["sha256"] = digest(path)
    try:
        frame = _validate_ohlc(pd.read_parquet(path))
        _, info = _minute_coverage(frame)
        record.update(info)
        record["status"] = "complete" if info["complete"] else "incomplete"
        record["timestamp_provenance"] = "legacy_minute_column_and_filename_date"
    except (ValueError, TypeError, OSError) as error:
        record.update(status="invalid", valid=False, error=str(error))
    return record


def build_plan(
    vt_source: Path = VT_SOURCE, native_root: Path = NATIVE_ROOT,
    protocol_path: Path = OUT / "PROTOCOL.md",
) -> dict[str, Any]:
    """Read all eligible VT dates and identify every missing/incomplete day before fetch."""
    vt = pd.read_csv(vt_source, usecols=["Date", "Vol Trigger"])
    parsed = pd.to_datetime(vt.Date, format="%Y-%m-%d", errors="raise").dt.date
    window = vt.loc[parsed.between(START, END)].copy()
    window["Date"] = parsed[parsed.between(START, END)].map(date.isoformat)
    if window.Date.duplicated().any():
        raise ValueError("Duplicate VT source dates in the frozen coverage window")
    trigger = pd.to_numeric(window["Vol Trigger"], errors="coerce")
    days = sorted(window.loc[np.isfinite(trigger) & trigger.gt(0), "Date"].tolist())
    existing = [_existing(native_root / f"{day}.parquet", day) for day in days]
    fetch_dates = [record["date"] for record in existing if not record["complete"]]
    if len(fetch_dates) > MAX_REQUESTS:
        raise ValueError(
            f"Coverage needs {len(fetch_dates)} requests; fixed maximum is {MAX_REQUESTS}"
        )
    return {
        "purpose": (
            "Complete native SPX coverage before random above-VT cohort sampling; no outcomes"
        ),
        "date_window": [START.isoformat(), END.isoformat()],
        "vt_source": str(vt_source), "vt_source_sha256": digest(vt_source),
        "protocol_path": str(protocol_path), "protocol_sha256": digest(protocol_path),
        "normalizer_path": str(Path(__file__).resolve()),
        "normalizer_sha256": digest(Path(__file__).resolve()),
        "legacy_cache_module": str(LEGACY_DOWNLOAD),
        "legacy_cache_sha256": digest(LEGACY_DOWNLOAD),
        "native_cache_root": str(native_root), "vt_dates": days, "existing": existing,
        "fetch_dates": fetch_dates, "maximum_explicit_data_requests": MAX_REQUESTS,
        "planned_requests_before_cache_reuse": len(fetch_dates),
        "sdk_workers": 2, "expected_rth_minutes": [570, 959], "expected_rth_rows": 390,
        "partial_sessions": "Preserve observed rows and mark incomplete; never fill or resample",
    }


def request_params(day: date) -> dict[str, Any]:
    return {
        "symbol": "SPX", "start_date": day, "end_date": day, "interval": "1m",
        "start_time": "09:30:00", "end_time": "16:00:00",
    }


def _json(path: Path, value: dict[str, Any]) -> None:
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    pending.replace(path)


def _freeze_plan(plan: dict[str, Any]) -> Path:
    path = OUT / "spx_coverage_plan.json"
    if path.exists() and json.loads(path.read_text()) != plan:
        raise ValueError("SPX coverage preflight plan changed; inspect before another collection")
    _json(path, plan)
    return path


def _store_normalized(
    frame: pd.DataFrame, day: str, raw_path: Path, info: dict[str, Any],
) -> dict[str, Any]:
    folder = DATA / "spx_normalized"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{day}.parquet"
    meta_path = path.with_suffix(".json")
    signature = {"raw_path": str(raw_path), "raw_sha256": digest(raw_path),
                 "normalizer_sha256": digest(Path(__file__).resolve())}
    if meta_path.exists():
        metadata = json.loads(meta_path.read_text())
        if (
            metadata["signature"] != signature or not path.exists()
            or digest(path) != metadata["sha256"]
        ):
            raise ValueError(f"Normalized cache changed: {path}")
        return metadata
    if path.exists():
        raise ValueError(f"Normalized cache exists without metadata: {path}")
    pending = path.with_suffix(".parquet.tmp")
    if pending.exists():
        raise ValueError(f"Incomplete normalized cache write: {pending}")
    frame.to_parquet(pending, index=False)
    pending.replace(path)
    metadata = {"path": str(path), "sha256": digest(path), "signature": signature, **info}
    _json(meta_path, metadata)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan-only", action="store_true", help="Write preflight plan; do not authenticate"
    )
    args = parser.parse_args()
    plan = build_plan()
    plan_path = _freeze_plan(plan)
    print(json.dumps({"phase": "preflight", "vt_dates": len(plan["vt_dates"]),
                      "fetch_dates": plan["fetch_dates"], "plan": str(plan_path)}), flush=True)
    if args.plan_only:
        return
    manifest: dict[str, Any] = {
        "plan_path": str(plan_path), "plan_sha256": digest(plan_path),
        "planned_dates": plan["fetch_dates"], "days": [], "status": "collecting", "at": now(),
    }
    manifest_path = OUT / "spx_coverage_download.json"
    _json(manifest_path, manifest)
    if not plan["fetch_dates"]:
        manifest.update(status="complete", at=now(), explicit_data_requests_used=0)
        _json(manifest_path, manifest)
        return
    spec = importlib.util.spec_from_file_location("frozen_sector_raw_cache", LEGACY_DOWNLOAD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cache = module.Cache(DATA / "spx_raw", limit=MAX_REQUESTS)
    logging.getLogger("thetadata").setLevel(logging.CRITICAL)
    cache.record({"status": "authentication_started"})
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from thetadata import ThetaClient
            client = ThetaClient(
                creds_file="/Users/dgrissen/Dev/ThetaData/creds.txt", dataframe_type="pandas"
            )
    except Exception as error:
        cache.record({"status": "authentication_error", "error_type": type(error).__name__})
        raise RuntimeError(f"Theta authentication: {type(error).__name__}") from None
    cache.record({"status": "authentication_ok"})

    def collect(day_string: str) -> dict[str, Any]:
        day = date.fromisoformat(day_string)
        record: dict[str, Any] = {"date": day_string, "complete": False}
        try:
            raw, raw_path = cache.get(
                "index_history_ohlc", request_params(day), client.index_history_ohlc
            )
            record.update(raw_path=str(raw_path), raw_sha256=digest(raw_path), raw_rows=len(raw))
            try:
                normalized, info = normalize_native(raw, day)
            except (ValueError, TypeError) as error:
                return record | {"status": "invalid", "valid": False,
                                 "normalization_error": str(error)}
            stored = _store_normalized(normalized, day_string, raw_path, info)
            return record | {"status": "complete" if info["complete"] else "partial",
                             **info, "normalized": stored}
        except (RuntimeError, ValueError, OSError) as error:
            return record | {"status": "error", "error": str(error)}

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(collect, day) for day in plan["fetch_dates"]]
        for future in as_completed(futures):
            record = future.result()
            manifest["days"].append(record)
            manifest.update(at=now(), explicit_data_requests_used=cache.used)
            _json(manifest_path, manifest)
            print(json.dumps({"phase": "coverage", "date": record["date"],
                              "status": record["status"], "complete": record["complete"],
                              "finished": len(manifest["days"]),
                              "planned": len(plan["fetch_dates"])}), flush=True)
    statuses = {record["status"] for record in manifest["days"]}
    manifest.update(status="complete_with_errors" if statuses & {"error", "invalid"}
                    else "complete_with_partial" if "partial" in statuses else "complete", at=now())
    _json(manifest_path, manifest)


if __name__ == "__main__":
    main()
