"""Causal XLRE acceleration magnitude; no outcome labels or trading decisions."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
DATA = Path("/Users/dgrissen/Dev/central_trade_data/thetadata/xlre_iv_magnitude_5d_2026-09-19-v1")
LEGACY = OUT.parent / "b06_sector_surface_50d_2026-09-13"
ET = "America/New_York"
EPS = 1e-12
HALF = (np.arange(15, dtype=float)-7)/280
ACCEL = np.r_[-HALF, HALF]/15


def make_plan() -> list[str]:
    """Fixed verified NYSE calendar: May 7 through August 10, 2026."""
    holidays = {"2026-05-25", "2026-06-19", "2026-07-03"}
    return [d for d in pd.bdate_range("2026-05-07", "2026-08-10").strftime("%Y-%m-%d")
            if d not in holidays]


def prior_sessions(sessions: list[str], day: str) -> list[str]:
    if sessions != sorted(set(sessions)):
        raise ValueError("Calendar must be sorted and unique")
    position = sessions.index(day)
    if position < 60:
        raise ValueError("Sixty prior sessions required")
    return sessions[position-60:position]


def block_id(end_min: int) -> int:
    if not 570 <= end_min <= 869:
        raise ValueError("Endpoint outside the fixed clock blocks")
    return (end_min-570)//60


def block_name(block: int) -> str:
    start = 570+60*block
    end = start+59
    return f"{start//60:02}:{start%60:02}–{end//60:02}:{end%60:02}"


def measure_day(surface: pd.DataFrame, day: str) -> pd.DataFrame:
    """Compute every exact thirty-minute window; missing minutes stay missing."""
    frame = surface.copy()
    stamps = pd.to_datetime(frame.timestamp)
    if not isinstance(stamps.dtype, pd.DatetimeTZDtype):
        raise ValueError("Timezone-aware minute timestamps required")
    stamps = stamps.dt.tz_convert(ET)
    if (stamps.duplicated().any() or not stamps.eq(stamps.dt.floor("min")).all()
            or not stamps.dt.strftime("%Y-%m-%d").eq(day).all()):
        raise ValueError("Duplicate, wrong-date or nonminute timestamps")
    frame["timestamp"] = stamps
    grid = pd.date_range(f"{day} 09:30", periods=300, freq="min", tz=ET)
    values = frame.set_index("timestamp").reindex(grid)[["atm", "atm_low", "atm_high"]].to_numpy(dtype=float)
    records = []
    for end in range(29, 300):
        window = values[end-29:end+1]
        valid = (np.isfinite(window).all() and (window[:, 0] > 0).all()
                 and (window[:, 1] <= window[:, 0]).all() and (window[:, 0] <= window[:, 2]).all())
        row = {"date": day, "start_min": 570+end-29, "end_min": 570+end,
               "block": block_id(570+end), "available": bool(valid),
               "b1": np.nan, "b2": np.nan, "acceleration": np.nan,
               "acceleration_low": np.nan, "acceleration_high": np.nan,
               "valid_minutes": int((np.isfinite(window).all(axis=1)
                   & (window[:, 0] > 0) & (window[:, 1] <= window[:, 0])
                   & (window[:, 0] <= window[:, 2])).sum())}
        if valid:
            row.update({"b1": float(HALF @ window[:15, 0]), "b2": float(HALF @ window[15:, 0]),
                        "acceleration": float(ACCEL @ window[:, 0]),
                        "acceleration_low": float(np.maximum(ACCEL, 0) @ window[:, 1]
                                                  + np.minimum(ACCEL, 0) @ window[:, 2]),
                        "acceleration_high": float(np.maximum(ACCEL, 0) @ window[:, 2]
                                                   + np.minimum(ACCEL, 0) @ window[:, 1])})
        row["falling_accelerating"] = bool(valid and row["b2"] < -EPS and row["acceleration"] < -EPS)
        row["negative_acceleration_quote_resolved"] = bool(valid and row["acceleration_high"] < -EPS)
        records.append(row)
    return pd.DataFrame(records)


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order])
    # Floating summation tolerance for the declared left-inverse CDF at an exact half.
    position = np.searchsorted(cumulative, cumulative[-1]/2 - 1e-14*cumulative[-1])
    return float(values[order[min(position, len(order)-1)]])


def robust_baseline(history: pd.DataFrame, dates: list[str], block: int) -> dict:
    """Equal total date weight, prior sessions only, signed acceleration history."""
    rows = history[history.date.isin(dates) & history.block.eq(block)
                   & history.available & np.isfinite(history.acceleration)].copy()
    counts = rows.groupby("date").size()
    result = {"history_days": len(counts), "history_windows": len(rows),
              "source_dates": counts.index.tolist(), "windows_by_date": counts.to_dict(),
              "median": np.nan, "mad": np.nan, "scale": np.nan,
              "status": "insufficient_history"}
    if len(counts) < 10:
        return result
    weights = rows.date.map(1/counts).to_numpy(dtype=float)/len(counts)
    values = rows.acceleration.to_numpy(dtype=float)
    center = weighted_median(values, weights)
    mad = weighted_median(np.abs(values-center), weights)
    scale = 1.4826*mad
    result.update({"median": center, "mad": mad, "scale": scale,
                   "status": "ok" if scale > EPS else "zero_or_tiny_scale"})
    return result


def score_window(b2: float, acceleration: float, scale: float) -> dict:
    if not all(np.isfinite(v) for v in [b2, acceleration, scale]) or scale <= EPS:
        return {"signed_score": np.nan, "downward_magnitude": np.nan}
    score = -acceleration/scale
    return {"signed_score": score,
            "downward_magnitude": score if b2 < -EPS and acceleration < -EPS else np.nan}


def main() -> None:
    manifest = json.loads((DATA / "manifest.json").read_text())
    if manifest["status"] != "complete":
        raise ValueError("Collection has not completed")
    sessions = make_plan()
    all_rows, coverage = [], []
    for record in manifest["days"]:
        day = record["date"]
        if record["status"] == "ok":
            surface = pd.read_parquet(record["surface_path"])
            atm_valid = int(surface.atm.notna().sum())
        else:
            surface = pd.DataFrame({"timestamp": pd.date_range(f"{day} 09:30", periods=300,
                                   freq="min", tz=ET), "atm": np.nan, "atm_low": np.nan, "atm_high": np.nan})
            atm_valid = 0
        measured = measure_day(surface, day)
        all_rows.append(measured)
        coverage.append({"date": day, "role": "pilot" if day in sessions[-5:] else "history",
                         "source_status": record["status"], "valid_atm_minutes": atm_valid,
                         "valid_acceleration_windows": int(measured.available.sum()),
                         "falling_accelerating_windows": int(measured.falling_accelerating.sum()),
                         "quote_resolved_negative_windows": int(measured.negative_acceleration_quote_resolved.sum()),
                         "reused_surface": record.get("reused_surface", False)})
    history = pd.concat(all_rows, ignore_index=True)
    if len(history) != 65*271 or set(history.date) != set(sessions):
        raise ValueError("Calendar coverage changed")
    history.to_parquet(DATA / "all_acceleration_windows.parquet", index=False)
    baselines, scored = [], []
    for day in sessions[-5:]:
        prior = prior_sessions(sessions, day)
        for block in range(5):
            stats = robust_baseline(history, prior, block)
            baseline = {"date": day, "block": block, "block_label": block_name(block),
                        "lookback_sessions": len(prior), "lookback_start": prior[0],
                        "lookback_end": prior[-1], **stats}
            baselines.append(baseline)
            rows = history[history.date.eq(day) & history.block.eq(block)]
            for row in rows.to_dict("records"):
                score = score_window(row["b2"], row["acceleration"], stats["scale"])
                status = ("missing_current_window" if not row["available"] else
                          stats["status"] if stats["status"] != "ok" else "ok")
                scored.append({**row, "history_days": stats["history_days"], "scale": stats["scale"],
                               **score, "score_status": status})
    serialized = [{**b, "source_dates": json.dumps(b["source_dates"]),
                   "windows_by_date": json.dumps(b["windows_by_date"])} for b in baselines]
    pd.DataFrame(serialized).to_csv(OUT / "block_baselines.csv", index=False)
    pd.DataFrame(coverage).to_csv(OUT / "coverage.csv", index=False)
    pilot = pd.DataFrame(scored)
    pilot.to_csv(OUT / "pilot_windows.csv", index=False)
    summary = pilot.groupby("date").agg(windows=("available", "size"),
            valid_accelerations=("available", "sum"), scored=("signed_score", "count"),
            falling_accelerating=("downward_magnitude", "count"),
            minimum_score=("signed_score", "min"), maximum_score=("signed_score", "max"))
    summary.to_csv(OUT / "pilot_summary.csv")
    print(summary.to_string())
    print(pd.DataFrame(baselines)[["date", "block_label", "history_days", "history_windows", "scale", "status"]].to_string(index=False))


if __name__ == "__main__":
    main()
