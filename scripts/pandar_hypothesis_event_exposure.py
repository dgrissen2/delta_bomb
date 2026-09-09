"""Measure observed short-cover losses at every captured NBBO event, not just minutes."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def event_cover_marks(frame: pd.DataFrame, opened: pd.Timestamp, end: pd.Timestamp,
                      sale_bid: float, slippage: float) -> pd.Series:
    """One assumed 100-share contract, firm positive ask with displayed size, RTH only."""
    stamp = pd.to_datetime(frame.timestamp)
    if stamp.dt.tz is None:
        stamp = stamp.dt.tz_localize("America/New_York")
    valid = (stamp.between(opened, end) & frame.bid.ge(0) & frame.ask.ge(frame.bid)
             & frame.ask.gt(0) & frame.ask_size.ge(1)
             & frame.bid_condition.isin([0, 50]) & frame.ask_condition.isin([0, 50]))
    return pd.Series(((sale_bid - frame.loc[valid, "ask"] - 2 * slippage) * 100 - 1.30).to_numpy(),
                     index=pd.DatetimeIndex(stamp[valid]))


def run(project: Path) -> None:
    out = project / "outputs/pandar_hypothesis_2026-09-07"
    table = pd.read_csv(out / "event_policy_replay.csv")
    table = table[table.initial_status.eq("entered") & table.slippage_per_share.eq(.01)].copy()
    records = [*json.loads((out / "entry_tick_history_manifest.json").read_text()),
               *json.loads((out / "tick_history_manifest.json").read_text())]
    outputs = []
    for (ticker, expiry, strike), group in table.groupby(["ticker", "expiry", "far_strike"]):
        manifests = {r["session"]: r for r in records if r["ticker"] == ticker and r["leg"] == "far"
                     and r["expiry"] == expiry and r["strike"] == strike}
        frames = {day: pd.read_parquet(r["path"]) for day, r in manifests.items() if r["status"] == "ok"}
        for row in group.to_dict("records"):
            opened = pd.Timestamp(row["entry_at"])
            paired = row.get("completion_status") == "completed"
            end = pd.Timestamp(row["conversion_at"] if paired else row["exit_at"])
            paths = []
            for day, frame in frames.items():
                if opened.strftime("%Y-%m-%d") <= day <= end.strftime("%Y-%m-%d"):
                    paths.append(event_cover_marks(frame, opened, end, row["entry_far_bid"], .01))
            marks = pd.concat(paths) if paths else pd.Series(dtype=float)
            worst = marks.min() if len(marks) else np.nan
            outputs.append({k: row[k] for k in ("variant", "ticker", "signal_date", "entry_policy",
                                                "method", "holding_sessions", "entry_at", "exit_at")} | {
                "short_phase_end": str(end), "counterfactual_unconverted_path": row.get("short_phase_is_counterfactual"),
                "valid_event_marks": len(marks), "worst_observed_event_cover_pnl": worst,
                "worst_event_at": str(marks.idxmin()) if len(marks) else None,
                "largest_observed_event_cover_loss": max(0., -worst) if len(marks) else np.nan,
                "minute_worst_cover_pnl": row.get("worst_observed_short_cover_pnl"),
                "basis": "Captured RTH NBBO quote events; no unobserved gap, overnight, assignment or maximum-loss inference"})
    pd.DataFrame(outputs).to_csv(out / "tick_short_phase_exposure.csv", index=False)


if __name__ == "__main__":
    run(Path.cwd())
