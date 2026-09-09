"""Local, exact-timestamp adapter for the frozen Pandar research population.

No provider calls. Interval quote samples are not quote-event timestamps. The default
run is a quoted-price diagnostic with assumed 100-share deliverables. A caller may
supply quote files containing genuine quote_timestamp fields and require_event_age
for a separate event-age replay; Greeks still join on their exact sample timestamps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

try:
    from scripts.pandar_hypothesis_replay import (
        FEE_PER_CONTRACT_ACTION, METHODS, PRIMARY_SLIPPAGE_PER_SHARE,
        STRESS_SLIPPAGE_PER_SHARE, FrozenCase, replay_case,
    )
except ModuleNotFoundError:
    from pandar_hypothesis_replay import (
        FEE_PER_CONTRACT_ACTION, METHODS, PRIMARY_SLIPPAGE_PER_SHARE,
        STRESS_SLIPPAGE_PER_SHARE, FrozenCase, replay_case,
    )

ZONE = "America/New_York"
RUN_NAME = "pandar_hypothesis_2026-09-07"
KNOWN_NO_SELECTION = frozenset({"no_expiry_in_dte_band", "no_call_in_delta_band",
                                "no_adjacent_nearer_strike", "nearer_not_otm"})
CASE_KEYS = ["variant", "ticker", "signal_date"]
GROUP_KEYS = ["variant", "entry_policy", "method", "holding_sessions", "slippage_per_share"]
ROW_KEYS = [*CASE_KEYS, *GROUP_KEYS[1:]]


def timestamp_index(values: Any) -> pd.DatetimeIndex:
    """Theta naive clocks are ET; aware clocks are converted, never reinterpreted."""
    stamps = []
    for value in values:
        stamp = pd.Timestamp(value)
        if pd.isna(stamp):
            raise ValueError("missing timestamp")
        stamps.append(stamp.tz_localize(ZONE) if stamp.tzinfo is None else stamp.tz_convert(ZONE))
    return pd.DatetimeIndex(stamps, tz=ZONE, name="timestamp")


def _indexed(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    values = result.pop("timestamp") if "timestamp" in result else result.index
    if not result.empty and not isinstance(values, (pd.Series, pd.DatetimeIndex)):
        raise ValueError("timestamp column or DatetimeIndex required")
    result.index = timestamp_index(values if len(result) else [])
    if result.index.duplicated().any():
        raise ValueError("duplicate source timestamps")
    for field in ("underlying_timestamp", "quote_timestamp", "bid_timestamp", "ask_timestamp"):
        if field in result:
            result[field] = result[field].map(
                lambda value: timestamp_index([value])[0] if pd.notna(value) else pd.NaT)
    return result.sort_index()


def merge_leg(quotes: pd.DataFrame, greeks: pd.DataFrame, leg: str, *,
              quote_source_path: str = "", greek_source_path: str = "") -> pd.DataFrame:
    """Outer exact join preserves absent evidence and each price's source."""
    if leg not in {"far", "near"}:
        raise ValueError("leg must be far or near")
    q, g = _indexed(quotes), _indexed(greeks)
    q["quote_source_path"] = quote_source_path
    g["greek_source_path"] = greek_source_path
    g["greek_timestamp"] = g.index
    # Embedded Greek prices cannot supply missing executable quotes.
    g = g.rename(columns={name: f"greek_{name}" for name in g.columns
                          if name in q.columns or name in {"bid", "ask"}})
    return q.join(g, how="outer", validate="one_to_one").add_prefix(f"{leg}_").sort_index()


def _manifest_index(manifest: list[dict[str, Any]]) -> dict[tuple[str, ...], dict[str, Any]]:
    result = {}
    for record in manifest:
        key = tuple(str(record[name]) for name in ("ticker", "signal_date", "leg", "kind"))
        if key in result:
            raise ValueError(f"duplicate manifest identity: {key}")
        result[key] = record
    return result


def _validate_contract(frame: pd.DataFrame, row: dict[str, Any], leg: str) -> None:
    if frame.empty:
        return
    required = {"symbol", "expiration", "strike", "right", "timestamp"}
    if not required.issubset(frame):
        raise ValueError("source contract identity fields missing")
    valid = (frame.symbol.eq(row["ticker"]).all()
             and frame.strike.eq(float(row[f"{leg}_strike"])).all()
             and frame.right.str.lower().isin(["call", "c"]).all()
             and pd.to_datetime(frame.expiration).dt.strftime("%Y-%m-%d").eq(row["expiry"]).all())
    if not valid:
        raise ValueError(f"source contract identity mismatch: {row['ticker']} {leg}")


def load_case_minutes(row: dict[str, Any], manifest: list[dict[str, Any]]) -> tuple[pd.DataFrame, list[str]]:
    """Read the four exact-contract files, retaining missing-file diagnostics."""
    records, errors, legs = _manifest_index(manifest), [], []
    for leg in ("far", "near"):
        frames, paths = {}, {}
        for kind in ("quote", "greeks_first_order"):
            record = records.get((row["ticker"], row["tradeDate"], leg, kind))
            frames[kind], paths[kind] = pd.DataFrame(), ""
            if record is None or record.get("status") != "ok":
                errors.append(f"{leg}_{kind}_manifest_unavailable")
                continue
            if (str(record.get("expiry")) != row["expiry"]
                    or float(record.get("strike", np.nan)) != float(row[f"{leg}_strike"])):
                raise ValueError("manifest contract identity mismatch")
            path = Path(record["path"])
            paths[kind] = str(path)
            if not path.is_file():
                errors.append(f"{leg}_{kind}_file_missing")
                continue
            frame = pd.read_parquet(path)
            _validate_contract(frame, row, leg)
            frames[kind] = frame
        legs.append(merge_leg(frames["quote"], frames["greeks_first_order"], leg,
                              quote_source_path=paths["quote"],
                              greek_source_path=paths["greeks_first_order"]))
    return legs[0].join(legs[1], how="outer", validate="one_to_one").sort_index(), errors


def earnings_statuses(ticker: str, days: list[str], events: pd.DataFrame,
                     coverage: pd.DataFrame) -> dict[str, str]:
    """Actual event dates only: inclusive [day, day+30], with full window coverage."""
    result = {day: "unknown" for day in days}
    required = {"ticker", "earnings_status", "earnings_coverage_start", "earnings_coverage_end"}
    if not required.issubset(coverage) or not {"ticker", "earnDate"}.issubset(events):
        return result
    match = coverage.loc[coverage.ticker.eq(ticker)]
    if len(match) != 1 or match.iloc[0].earnings_status != "ok":
        return result
    start = pd.to_datetime(match.iloc[0].earnings_coverage_start, errors="coerce")
    end = pd.to_datetime(match.iloc[0].earnings_coverage_end, errors="coerce")
    dates = pd.to_datetime(events.loc[events.ticker.eq(ticker), "earnDate"], errors="coerce")
    if pd.isna(start) or pd.isna(end) or dates.isna().any() or dates.empty:
        return result
    for day in days:
        current = pd.Timestamp(day)
        cutoff = current + pd.Timedelta(days=30)
        if start <= current and cutoff <= end:
            result[day] = "event_in_next_30_days" if dates.between(current, cutoff).any() else "clear"
    return result


def unavailable_case_rows(row: dict[str, Any], variant: str, reason: str, *,
                          known_no_entry: bool) -> pd.DataFrame:
    """Keep all policy slots when a frozen contract or necessary input is absent."""
    rows, pnl = [], 0. if known_no_entry else np.nan
    for policy in ("clock", "hiro"):
        for horizon in (4, 5):
            deadline = row.get(f"holding_session_{horizon}")
            expiry = row.get("expiry")
            if pd.notna(expiry) and deadline:
                deadline = min(str(expiry), deadline)
            for method in METHODS:
                for cost in (PRIMARY_SLIPPAGE_PER_SHARE, STRESS_SLIPPAGE_PER_SHARE):
                    result = dict(ticker=row["ticker"], signal_date=row["tradeDate"],
                                  entry_date=row["entry_date"], expiry=expiry,
                                  far_strike=row.get("far_strike"), near_strike=row.get("near_strike"),
                                  variant=variant, entry_policy=policy, method=method,
                                  holding_sessions=horizon, slippage_per_share=cost,
                                  exit_at=str(pd.Timestamp(f"{deadline} 15:50", tz=ZONE)) if deadline else None,
                                  initial_status="known_no_entry" if known_no_entry else "censored_entry",
                                  initial_reason=reason, pnl_net=pnl,
                                  multiplier=100., multiplier_verified=False, deliverables_verified=False,
                                  quote_event_age_verified=False, executable_inference_verified=False,
                                  inference_basis="Quoted-price diagnostic; event ages and deliverables unverified",
                                  fee_per_contract_action=FEE_PER_CONTRACT_ACTION,
                                  executed_actions=0, reserved_actions=0,
                                  cover_at_conversion_status="no_entry_zero_policy" if known_no_entry else "not_applicable")
                    for name in ("immediate_spread_pnl", "short_only_pnl", "cover_at_conversion_pnl",
                                 "incremental_vs_immediate_spread", "incremental_vs_short_only",
                                 "incremental_vs_conversion_cover"):
                        result[name] = pnl
                    rows.append(result)
    return pd.DataFrame(rows)


def replay_population(cases: pd.DataFrame, manifest: list[dict[str, Any]], hiro: pd.DataFrame,
                      events: pd.DataFrame, coverage: pd.DataFrame, *, variant: str,
                      require_event_age: bool = False,
                      minute_transform: Callable[[dict[str, Any], pd.DataFrame], pd.DataFrame] | None = None,
                      ) -> pd.DataFrame:
    """Every frozen episode contributes 40 rows, including zero and censored outcomes."""
    if cases.duplicated(["ticker", "tradeDate"]).any():
        raise ValueError("duplicate population episode")
    _manifest_index(manifest)
    bounds = (.02, .10, 0.) if variant == "original" else (.05, .15, 5.)
    if variant not in {"original", "delta10_otm5", "delta_5_15_otm5"}:
        raise ValueError("unrecognized frozen variant")
    outputs = []
    for row in cases.to_dict("records"):
        errors = []
        if row["selection_status"] != "selected":
            table = unavailable_case_rows(row, variant, row["selection_status"],
                                          known_no_entry=row["selection_status"] in KNOWN_NO_SELECTION)
        else:
            sessions = tuple(row[f"holding_session_{index}"] for index in range(1, 6))
            statuses = earnings_statuses(row["ticker"], [row["tradeDate"], *sessions], events, coverage)
            minutes, errors = load_case_minutes(row, manifest)
            if minute_transform is not None:
                minutes = minute_transform(row, minutes)
            case = FrozenCase(ticker=row["ticker"], signal_date=row["tradeDate"],
                              entry_date=row["entry_date"], expiry=row["expiry"],
                              far_strike=float(row["far_strike"]), near_strike=float(row["near_strike"]),
                              exchange_sessions=sessions, earnings_status_by_date=statuses,
                              variant=variant, far_delta_min=bounds[0], far_delta_max=bounds[1],
                              far_otm_min_pct=bounds[2], require_event_age=require_event_age)
            decisions = hiro.copy()
            if not decisions.empty:
                decisions = decisions.loc[decisions.ticker.eq(row["ticker"])]
                if "session_date" in decisions:
                    decisions = decisions.loc[decisions.session_date.eq(row["entry_date"])]
            # Frozen population already screened the signal. Recheck actual metadata
            # and let the replay distinguish observed failures from missing entry inputs.
            table = replay_case(case, minutes, decisions)
            signal_status = statuses[row["tradeDate"]]
            if signal_status != "clear":
                table = unavailable_case_rows(row, variant, f"signal_earnings_{signal_status}",
                                              known_no_entry=signal_status == "event_in_next_30_days")
        table["selection_status"] = row["selection_status"]
        table["source_errors"] = json.dumps(errors)
        table["source_paths"] = json.dumps([record.get("path") for record in manifest
                                            if record["ticker"] == row["ticker"]
                                            and record["signal_date"] == row["tradeDate"]])
        table["require_event_age"] = require_event_age
        table["earnings_policy"] = "retrospective_actual_event_exclusion_not_PIT_schedule"
        if len(table) != 40:
            raise ValueError("replay must retain 40 policy rows per episode")
        outputs.append(table)
    return pd.concat(outputs, ignore_index=True) if outputs else pd.DataFrame()


def _paired(frame: pd.DataFrame, reference: str) -> dict[str, Any]:
    pair = frame.loc[np.isfinite(frame.pnl_net) & np.isfinite(frame[reference])]
    difference = pair.pnl_net - pair[reference]
    return {"population_cases": len(frame), "paired_cases": len(pair),
            "unpaired_cases": len(frame) - len(pair),
            "paired_distinct_dates": int(pair.entry_date.nunique()),
            "mean_difference": float(difference.mean()) if len(pair) else None,
            "median_difference": float(difference.median()) if len(pair) else None}


def summarize_replay(table: pd.DataFrame) -> dict[str, Any]:
    """Exact episode pairing; missing paths never become zeros or extra observations."""
    if table.duplicated(ROW_KEYS).any():
        raise ValueError("duplicate replay episode/policy weights")
    groups = []
    for keys, frame in table.groupby(GROUP_KEYS, dropna=False, sort=True):
        priced = frame.loc[np.isfinite(frame.pnl_net)]
        group = dict(zip(GROUP_KEYS, keys, strict=True))
        group.update(population_cases=len(frame), priced_cases=len(priced),
                     censored_cases=len(frame) - len(priced),
                     known_no_entry_cases=int(frame.initial_status.eq("known_no_entry").sum()),
                     entered_cases=int(frame.initial_status.eq("entered").sum()),
                     priced_entered_cases=int(priced.initial_status.eq("entered").sum()),
                     mean_pnl_priced=float(priced.pnl_net.mean()) if len(priced) else None,
                     median_pnl_priced=float(priced.pnl_net.median()) if len(priced) else None,
                     initial_reasons=frame.initial_reason.fillna("").value_counts().to_dict(),
                     comparisons={name: _paired(frame, column) for name, column in
                                  [("immediate_spread", "immediate_spread_pnl"),
                                   ("short_only", "short_only_pnl"),
                                   ("conversion_cover", "cover_at_conversion_pnl")]})
        for column in ("completion_status", "exit_status", "cover_at_conversion_status"):
            if column in frame:
                group[column + "_counts"] = frame[column].fillna("not_applicable").value_counts().to_dict()
        groups.append(group)
    pairing_keys = [*CASE_KEYS, "entry_date", "method", "holding_sessions", "slippage_per_share"]
    clock = table.loc[table.entry_policy.eq("clock"), pairing_keys + ["pnl_net"]]
    clock = clock.rename(columns={"pnl_net": "clock_pnl"})
    paired = table.loc[table.entry_policy.eq("hiro")].merge(clock, on=pairing_keys,
                                                          how="outer", validate="one_to_one")
    entry_groups = []
    columns = ["variant", "method", "holding_sessions", "slippage_per_share"]
    for keys, frame in paired.groupby(columns, sort=True):
        entry_groups.append(dict(zip(columns, keys, strict=True)) | _paired(frame, "clock_pnl"))
    dates = int(table.entry_date.nunique())
    return {"rows": len(table), "population_by_variant": table[CASE_KEYS].drop_duplicates().groupby("variant").size().to_dict(),
            "distinct_entry_dates": dates, "minimum_distinct_dates_required": 20,
            "statistical_support": "inconclusive_fewer_than_20_dates" if dates < 20 else "descriptive_only",
            "inference_basis": "Minute quoted-price diagnostic; no verified quote event age, deliverables or assignment model",
            "aggregation": "Equal episode weights; finite paired P&L only; known no-entry zero; missing evidence NaN",
            "pnl_units": "USD per one assumed 100-share option contract",
            "earnings_policy": "Retrospective actual events, inclusive next 30 calendar days; not PIT schedules",
            "policy_groups": groups, "entry_policy_comparisons": entry_groups}


def admitted_case_comparisons(table: pd.DataFrame) -> pd.DataFrame:
    """One row per admitted policy and D4/D5 deadline under the primary cost."""
    admitted = table.loc[table.initial_status.eq("entered")
                         & table.slippage_per_share.eq(PRIMARY_SLIPPAGE_PER_SHARE)]
    keys = [*CASE_KEYS, "entry_policy", "holding_sessions"]
    rows = []
    for values, frame in admitted.groupby(keys, sort=True):
        first = frame.iloc[0]
        row = dict(zip(keys, values, strict=True))
        for name in ("entry_date", "entry_at", "exit_at", "expiry", "far_strike", "near_strike",
                     "entry_far_delta", "entry_far_otm_pct", "entry_far_bid", "entry_far_ask"):
            row[name] = first.get(name)
        for _, arm in frame.iterrows():
            prefix = arm["method"]
            for name in ("pnl_net", "completion_status", "conversion_at", "exit_status",
                         "cover_at_conversion_pnl", "incremental_vs_conversion_cover"):
                row[f"{prefix}_{name}"] = arm.get(name)
        rows.append(row)
    return pd.DataFrame(rows)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_inputs(out: Path) -> None:
    """Read-only verification of existing freezes; never rewrite their provenance."""
    for name, fields in [("contract_freeze.json", ("sha256", "source_hashes")),
                          ("before_outcome_histories.json", ("hashes",)),
                          ("variant_freeze.json", ("hashes",))]:
        record = json.loads((out / name).read_text())
        for field in fields:
            for filename, expected in record[field].items():
                if _sha(Path(filename)) != expected:
                    raise ValueError(f"frozen input changed: {filename}")


def run(project: Path) -> dict[str, Any]:
    """Run both complete local manifests; preserve every frozen population member."""
    out, data = project / "outputs" / RUN_NAME, project / "data" / RUN_NAME
    verify_frozen_inputs(out)
    paths = [out / "frozen_contract_selections.csv", out / "variant_frozen_contracts.csv",
             out / "minute_history_manifest.json", out / "variant_minute_history_manifest.json",
             out / "hiro_pre_august_decisions.parquet", data / "earnings.parquet", data / "metadata_coverage.csv",
             Path(__file__), Path(__file__).with_name("pandar_hypothesis_replay.py")]
    hashes = {str(path): _sha(path) for path in paths}
    originals, variants = (pd.read_csv(path) for path in paths[:2])
    if len(originals) != 50 or len(variants) != 50 or set(zip(originals.ticker, originals.tradeDate)) != set(zip(variants.ticker, variants.tradeDate)):
        raise ValueError("both arms must retain the same frozen 50 episodes")
    hiro, events, coverage = pd.read_parquet(paths[4]), pd.read_parquet(paths[5]), pd.read_csv(paths[6])
    tables = []
    for cases, path, variant in [(originals, paths[2], "original"), (variants, paths[3], "delta10_otm5")]:
        manifest = json.loads(path.read_text())
        if len(manifest) != 4 * cases.selection_status.eq("selected").sum() or any(record["status"] != "ok" for record in manifest):
            raise ValueError(f"complete quote/Greek manifest required: {path}")
        for record in manifest:
            hashes[record["path"]] = _sha(Path(record["path"]))
        tables.append(replay_population(cases, manifest, hiro, events, coverage, variant=variant))
    table = pd.concat(tables, ignore_index=True)
    summary = summarize_replay(table)
    summary["source_sha256"] = hashes
    summary["created_at_utc"] = pd.Timestamp.now(tz="UTC").isoformat()
    summary["minute_event_ages_verified"] = False
    summary["contract_deliverables_verified"] = False
    summary["variant_overlap_previously_acquired_legs"] = 11
    for filename, digest in hashes.items():
        if _sha(Path(filename)) != digest:
            raise ValueError(f"input changed during replay: {filename}")
    table.to_csv(out / "policy_replay.csv", index=False)
    admitted_case_comparisons(table).to_csv(out / "admitted_case_comparisons.csv", index=False)
    (out / "replay_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return {"rows": len(table), "distinct_entry_dates": summary["distinct_entry_dates"],
            "population_by_variant": summary["population_by_variant"],
            "entered_case_policies": len(table.loc[table.initial_status.eq("entered"),
                                                   [*CASE_KEYS, "entry_policy"]].drop_duplicates()),
            "output": str(out / "policy_replay.csv")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.project.resolve()), indent=2))
