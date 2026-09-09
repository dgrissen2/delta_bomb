"""Bounded descriptive resampling of the frozen five-entry-session research sample.

The complete cross-section and its episode/policy pairs move together in the one
chronological five-session block. Drawing that single block 2,000 times is explicitly
degenerate. Empirical bootstrap quantiles are reported as arithmetic diagnostics,
never as a confidence interval or a statistical pass. No model fitting or tuning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

CASE = ["variant", "ticker", "signal_date"]
PAIR = [*CASE, "entry_date", "entry_policy", "holding_sessions", "slippage_per_share"]
GROUP = ["variant", "entry_policy", "method", "holding_sessions", "slippage_per_share", "comparison"]
METHODS = frozenset({"immediate_spread", "deferred_d0", "deferred_d1", "deferred_d2", "short_only"})
RUN_NAME = "pandar_hypothesis_2026-09-07"


def comparison_pairs(table: pd.DataFrame) -> pd.DataFrame:
    """Pair actual control rows by episode; retain NaN rows in every denominator."""
    required = {*PAIR, "method", "pnl_net", "cover_at_conversion_pnl"}
    if not required.issubset(table):
        raise ValueError(f"missing replay columns: {sorted(required - set(table.columns))}")
    if table.duplicated([*PAIR, "method"]).any():
        raise ValueError("duplicate replay episode/policy")
    if not table.groupby(CASE).size().eq(40).all():
        raise ValueError("each episode must retain all 40 policy slots")
    if (set(table.method) != METHODS or set(table.entry_policy) != {"clock", "hiro"}
            or set(table.holding_sessions) != {4, 5} or set(table.slippage_per_share) != {.01, .02}):
        raise ValueError("unexpected frozen method, policy, horizon or cost")
    if not table.groupby(CASE).entry_date.nunique().eq(1).all():
        raise ValueError("episode has inconsistent entry dates")
    arms = table.loc[table.method.isin(["deferred_d0", "deferred_d1", "deferred_d2"]),
                     [*PAIR, "method", "pnl_net", "cover_at_conversion_pnl"]]
    outputs = []
    for control in ("immediate_spread", "short_only", "conversion_cover"):
        if control == "conversion_cover":
            joined = arms.rename(columns={"cover_at_conversion_pnl": "reference_pnl"})
        else:
            reference = table.loc[table.method.eq(control), [*PAIR, "pnl_net"]]
            reference = reference.rename(columns={"pnl_net": "reference_pnl"})
            joined = arms.merge(reference, on=PAIR, how="left", validate="many_to_one")
        joined = joined.copy()
        joined["comparison"] = joined.method + f"_minus_{control}"
        outputs.append(joined)
    policy_keys = [name for name in PAIR if name != "entry_policy"] + ["method"]
    clock = table.loc[table.entry_policy.eq("clock"), [*policy_keys, "pnl_net"]]
    clock = clock.rename(columns={"pnl_net": "reference_pnl"})
    hiro = table.loc[table.entry_policy.eq("hiro"), [*PAIR, "method", "pnl_net"]]
    joined = hiro.merge(clock, on=policy_keys, how="outer", validate="one_to_one")
    joined["comparison"], joined["entry_policy"] = "hiro_minus_clock", "hiro_minus_clock"
    outputs.append(joined)
    pairs = pd.concat(outputs, ignore_index=True)
    pairs["fully_priced_pair"] = np.isfinite(pairs.pnl_net) & np.isfinite(pairs.reference_pnl)
    pairs["difference"] = (pairs.pnl_net - pairs.reference_pnl).where(pairs.fully_priced_pair)
    return pairs


def resample_comparisons(table: pd.DataFrame, calendar: list[str], *,
                         repetitions: int = 2000, seed: int = 20260907) -> dict[str, Any]:
    """Actually draw 2,000 blocks; the sole supported block repeats the whole sample."""
    if calendar != sorted(set(calendar)):
        raise ValueError("calendar must be chronological and unique")
    if len(calendar) != 5 or set(table.entry_date) != set(calendar):
        raise ValueError("this bounded analysis requires exactly the frozen five entry sessions")
    if repetitions != 2000:
        raise ValueError("the frozen repetition count is 2000")
    pairs = comparison_pairs(table)
    # One shared draw sequence retains cross-comparison and cross-sectional pairing.
    draws = np.random.default_rng(seed).integers(0, 1, size=(repetitions, 1))
    groups = []
    for key, frame in pairs.groupby(GROUP, sort=True):
        values = frame.loc[frame.fully_priced_pair, "difference"].to_numpy(dtype=float)
        count = len(values)
        mean = float(values.mean()) if count else None
        median = float(np.median(values)) if count else None
        # Block lookup applies to the entire cross-section, never individual rows.
        sums = np.array([values.sum()], dtype=float)[draws].sum(axis=1)
        counts = np.array([count], dtype=int)[draws].sum(axis=1)
        means = np.divide(sums, counts, out=np.full(repetitions, np.nan), where=counts > 0)
        medians = np.array([median if count else np.nan], dtype=float)[draws[:, 0]]
        record = dict(zip(GROUP, key, strict=True))
        record.update(
            population_cases=len(frame), paired_cases=count, unpaired_cases=len(frame) - count,
            paired_distinct_dates=int(frame.loc[frame.fully_priced_pair, "entry_date"].nunique()),
            population_by_date=frame.groupby("entry_date").size().reindex(calendar, fill_value=0).to_dict(),
            paired_by_date=frame.loc[frame.fully_priced_pair].groupby("entry_date").size().reindex(calendar, fill_value=0).to_dict(),
            mean_difference=mean, median_difference=median,
            priced_replicates=int(np.isfinite(means).sum()),
            bootstrap_unique_means=len(np.unique(means[np.isfinite(means)])),
            bootstrap_mean_quantiles=np.quantile(means, [.0125, .9875]).tolist() if count else None,
            bootstrap_median_quantiles=np.quantile(medians, [.0125, .9875]).tolist() if count else None,
            confidence_interval=None, statistical_pass=False,
            reason="One five-session block and fewer than 20 dates; repeated sample is not independent evidence",
        )
        groups.append(record)
    return {
        "method": "Shared chronological five-session block bootstrap, complete date cross-sections and episode pairs",
        "calendar": calendar, "calendar_basis": "Frozen exchange entry-session dates, not calendar-day spacing",
        "block_sessions": 5, "complete_five_session_blocks": 1,
        "blocks": [{"block_id": 0, "sessions": calendar}], "replicates": repetitions,
        "seed": seed, "block_draw_counts": {"0": int(draws.size)},
        "block_draw_sha256": hashlib.sha256(draws.astype("<i8").tobytes()).hexdigest(),
        "degenerate_resampling": True, "statistical_pass": False,
        "minimum_distinct_dates_required": 20,
        "interpretation": "2,000 draws repeat one complete block. Quantiles are degenerate arithmetic diagnostics, not confidence intervals. No significance claim is supported.",
        "missingness": "Only fully priced episode pairs enter each mean/median; all cases remain in coverage denominators. Known no-entry zeros remain zeros.",
        "units": "USD per one assumed 100-share option contract; economic execution and deliverables remain separate gates",
        "additional_sensitivity": "None; no independent-date resampling substituted for the frozen block rule",
        "comparisons": groups,
    }


def run(project: Path, input_path: Path | None = None, output_path: Path | None = None) -> dict[str, Any]:
    out = project / "outputs" / RUN_NAME
    source = input_path or out / "event_policy_replay.csv"
    target = output_path or project / "outputs" / "block_resampling.json"
    frozen_path = out / "frozen_contract_selections.csv"
    frozen = pd.read_csv(frozen_path)
    calendar = sorted(frozen.entry_date.unique().tolist())
    table = pd.read_csv(source)
    frozen_cases = set(zip(frozen.ticker, frozen.tradeDate))
    if len(frozen_cases) != 50 or set(table.variant) != {"original", "delta10_otm5"}:
        raise ValueError("resampling requires both complete frozen 50-case research arms")
    for _, group in table.groupby("variant"):
        if set(zip(group.ticker, group.signal_date)) != frozen_cases:
            raise ValueError("event replay population differs from the frozen 50 cases")
    result = resample_comparisons(table, calendar)
    result["source_sha256"] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in (source, frozen_path, Path(__file__))}
    result["created_at_utc"] = pd.Timestamp.now(tz="UTC").isoformat()
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return {"output": str(target), "comparisons": len(result["comparisons"]),
            "replicates": result["replicates"], "statistical_pass": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.project.resolve(), args.input, args.output), indent=2))
