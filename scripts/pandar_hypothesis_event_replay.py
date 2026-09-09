"""Overlay real NBBO events causally, retaining minute Greeks without filling them."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

QUOTE_FIELDS = ("bid", "ask", "bid_size", "ask_size", "bid_condition", "ask_condition",
                "bid_exchange", "ask_exchange")


def overlay_events(minutes: pd.DataFrame, records: list[dict[str, Any]],
                   *, frames: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Use the last actual event at or before each order, scoped to that captured session.

    Missing/empty session histories stay missing. No prior-day events cross that boundary.
    A minute sample label is never represented as a quote-event timestamp.
    """
    result = minutes.copy()
    if not isinstance(result.index, pd.DatetimeIndex) or result.index.tz is None:
        raise ValueError("minute index must be timezone-aware")
    sessions = result.index.tz_convert("America/New_York").strftime("%Y-%m-%d")
    for leg in ("far", "near"):
        for field in QUOTE_FIELDS:
            column = f"{leg}_{field}"
            if column in result:
                result[f"{leg}_interval_{field}"] = result[column]
            result[column] = np.nan
        result[f"{leg}_quote_timestamp"] = pd.Series(pd.NaT, index=result.index,
                                                     dtype="datetime64[ns, America/New_York]")
        result[f"{leg}_quote_source_path"] = pd.Series(None, index=result.index, dtype=object)
        result[f"{leg}_event_history_status"] = "not_requested"
        for record in (r for r in records if r["leg"] == leg):
            mask = sessions == record["session"]
            result.loc[mask, f"{leg}_event_history_status"] = record["status"]
            if not mask.any() or record["status"] != "ok":
                continue
            frame = frames[record["path"]].copy() if frames is not None else pd.read_parquet(record["path"])
            events = pd.to_datetime(frame.timestamp)
            if events.dt.tz is None:
                events = events.dt.tz_localize("America/New_York")
            else:
                events = events.dt.tz_convert("America/New_York")
            if not events.dt.strftime("%Y-%m-%d").eq(record["session"]).all():
                raise ValueError("event file contains another ET session")
            frame["event_timestamp"] = events.astype("datetime64[ns, America/New_York]")
            # Same-time messages retain provider order; the last observed NBBO prevails.
            frame = frame.sort_values("event_timestamp", kind="stable").drop_duplicates("event_timestamp", keep="last")
            left = pd.DataFrame({"order_timestamp": result.index[mask].as_unit("ns")}).sort_values("order_timestamp")
            right = frame[["event_timestamp", *[c for c in QUOTE_FIELDS if c in frame]]]
            merged = pd.merge_asof(left, right, left_on="order_timestamp", right_on="event_timestamp",
                                   direction="backward", allow_exact_matches=True).set_index("order_timestamp")
            for field in QUOTE_FIELDS:
                if field in merged:
                    result.loc[merged.index, f"{leg}_{field}"] = merged[field].to_numpy()
            result.loc[merged.index, f"{leg}_quote_timestamp"] = merged.event_timestamp
            result.loc[merged.index, f"{leg}_quote_source_path"] = record["path"]
    return result


def run(project: Path) -> dict[str, Any]:
    """Replay the full frozen denominator with real event evidence where acquired."""
    from scripts.pandar_hypothesis_run import (
        RUN_NAME, admitted_case_comparisons, replay_population, summarize_replay, verify_frozen_inputs,
    )

    out, data = project / "outputs" / RUN_NAME, project / "data" / RUN_NAME
    verify_frozen_inputs(out)
    entries = json.loads((out / "entry_tick_history_manifest.json").read_text())
    holding = json.loads((out / "tick_history_manifest.json").read_text())
    hiro = pd.read_parquet(out / "hiro_pre_august_decisions.parquet")
    events, coverage = pd.read_parquet(data / "earnings.parquet"), pd.read_csv(data / "metadata_coverage.csv")
    tables, sources = [], {}
    for variant in ("original", "delta10_otm5"):
        pairs = pd.read_csv(out / ("frozen_contract_selections.csv" if variant == "original" else "variant_frozen_contracts.csv"))
        manifest = json.loads((out / ("minute_history_manifest.json" if variant == "original" else "variant_minute_history_manifest.json")).read_text())

        def transform(row: dict[str, Any], minutes: pd.DataFrame) -> pd.DataFrame:
            matching = {}
            for record in [*entries, *holding]:
                if (record["ticker"] == row["ticker"] and record["signal_date"] == row["tradeDate"]
                        and record["expiry"] == row["expiry"]
                        and float(record["strike"]) == float(row[f"{record['leg']}_strike"])):
                    key = (record["leg"], record["session"])
                    if key in matching and matching[key].get("path") != record.get("path"):
                        raise ValueError("conflicting event session histories")
                    matching[key] = record
                    if record.get("path"):
                        path = Path(record["path"])
                        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            return overlay_events(minutes, list(matching.values()))

        tables.append(replay_population(pairs, manifest, hiro, events, coverage, variant=variant,
                                        require_event_age=True, minute_transform=transform))
    table = pd.concat(tables, ignore_index=True)
    summary = summarize_replay(table)
    summary["inference_basis"] = "Actual NBBO event quotes at most five seconds old; exact minute Greeks; assumed 100-share deliverables remain unverified"
    summary["event_source_sha256"] = sources
    summary["entry_event_manifest_records"] = len(entries)
    summary["holding_event_manifest_records"] = len(holding)
    summary["contract_deliverables_verified"] = False
    summary["created_at_utc"] = pd.Timestamp.now(tz="UTC").isoformat()
    table.to_csv(out / "event_policy_replay.csv", index=False)
    admitted_case_comparisons(table).to_csv(out / "event_admitted_case_comparisons.csv", index=False)
    (out / "event_replay_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return {"rows": len(table), "entered": table.loc[table.initial_status.eq("entered"),
                                                     ["variant", "ticker", "entry_policy"]].drop_duplicates().to_dict("records")}


if __name__ == "__main__":
    print(json.dumps(run(Path.cwd()), indent=2))
