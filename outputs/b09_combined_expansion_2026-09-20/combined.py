"""One fixed union of previously frozen admissions; no new signal generation."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
PREVIOUS_CODE = OUT.parent / "b09_opportunity_expansion_2026-09-20"
sys.path.insert(0, str(PREVIOUS_CODE))
from analyze import daily, summary_row  # noqa: E402
from study import HALVES, describe, difference, digest, keys, thin, write_json  # noqa: E402

ROOT = Path("/Users/dgrissen/Dev/central_trade_data/thetadata")
SOURCE = ROOT / "b09_opportunity_expansion_2026-09-20-v1"
PRIOR = ROOT / "mad_transfer_spx_2026-09-20-v1"
DATA = ROOT / "b09_combined_expansion_2026-09-20-v1"
FLAGS = ["baseline", "b05_candidate", "persistence_candidate", "b07_candidate"]
KEY = ["date", "known_min"]


def aggregate_routes(parents: pd.DataFrame) -> pd.DataFrame:
    """Retain all admission identities at one executable minute, before outcomes."""
    if parents[FLAGS].isna().any().any():
        raise ValueError("Missing frozen admission flag")
    if any(parents[c].dtype != bool for c in FLAGS):
        raise ValueError("Admission flags must be boolean")
    selected = parents.loc[parents[FLAGS].any(axis=1)].copy()
    if selected.groupby(KEY).half.nunique().gt(1).any():
        raise ValueError("Conflicting half-year")
    grouped = selected.groupby(KEY, sort=True)
    result = grouped.agg(
        **{c: (c, "max") for c in FLAGS},
        half=("half", "first"),
        parent_ids=("entry_id", lambda s: "|".join(sorted(set(s)))),
    ).reset_index()
    result["added"] = ~result.baseline
    result["route_pattern"] = result.apply(
        lambda r: "+".join(
            name
            for flag, name in zip(
                FLAGS[1:], ["B05", "B09_persistence", "B07"], strict=True
            )
            if r[flag]
        ),
        axis=1,
    )
    return result


def attach_outcomes(routes: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """Require duplicate parents to have identical prices and barrier outcomes."""
    columns = ["outcome", "entry_price", "first_touch_min"]
    for col in columns:
        if outcomes.groupby(KEY)[col].nunique(dropna=False).gt(1).any():
            raise ValueError(f"Conflicting duplicate {col}")
    result = routes.merge(
        outcomes[KEY + columns].drop_duplicates(KEY),
        on=KEY,
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if not result._merge.eq("both").all() or result.outcome.isna().any():
        raise ValueError("Missing outcome for selected execution")
    return result.drop(columns="_merge")


def prepare() -> None:
    """Freeze outcome-free combined membership; existing results were already known."""
    DATA.mkdir(exist_ok=True)
    if (DATA / "freeze.json").exists():
        raise FileExistsError("Combined freeze already exists")
    old = json.loads((SOURCE / "freeze.json").read_text())
    receipt = json.loads((SOURCE / "analysis_receipt.json").read_text())
    inputs = {}
    for name in ["memberships.parquet", "research_dates.csv"]:
        path = SOURCE / name
        assert digest(path) == old["outputs"][str(path)]
        inputs[str(path)] = digest(path)
    for path, expected in receipt["outcome_source"].items():
        assert digest(Path(path)) == expected
        inputs[path] = expected
    path = SOURCE / "summary.csv"
    assert digest(path) == receipt["outputs"][str(path)]
    inputs[str(path)] = digest(path)
    parents = pd.read_parquet(SOURCE / "memberships.parquet")
    assert len(parents) == 5093 and not parents.entry_id.duplicated().any()
    assert parents.loc[parents.baseline, "persistence_candidate"].all()
    routes = aggregate_routes(parents)
    calendar = pd.read_csv(SOURCE / "research_dates.csv")
    assert len(calendar) == 239 and set(routes.date).issubset(set(calendar.date))
    routes.to_parquet(DATA / "memberships.parquet", index=False)
    (DATA / "research_dates.csv").write_bytes(
        (SOURCE / "research_dates.csv").read_bytes()
    )
    code = [
        OUT / "combined.py",
        OUT / "PROTOCOL.md",
        PREVIOUS_CODE / "study.py",
        PREVIOUS_CODE / "analyze.py",
    ]
    write_json(
        DATA / "freeze.json",
        dict(
            inputs=inputs,
            code_protocol={str(p): digest(p) for p in code},
            outputs={
                str(DATA / n): digest(DATA / n)
                for n in ["memberships.parquet", "research_dates.csv"]
            },
            outcome_free=True,
            reused_previously_scored_components=True,
            combined_n=len(routes),
        ),
    )
    print(f"Frozen {len(routes)} unique execution timestamps; no outcome join.")


def run() -> None:
    """Score the declared union, retaining additions, overlaps and displacements."""
    freeze = json.loads((DATA / "freeze.json").read_text())
    for group in ["inputs", "outputs", "code_protocol"]:
        for path, expected in freeze[group].items():
            assert digest(Path(path)) == expected, path
    outcomes = pd.read_parquet(PRIOR / "events_with_outcomes.parquet")
    routes = pd.read_parquet(DATA / "memberships.parquet")
    events = attach_outcomes(routes, outcomes)
    events["entry_time_et"] = events.known_min.map(
        lambda m: f"{m // 60:02}:{m % 60:02}"
    )
    base = events[events.baseline].copy()
    added = events[events.added].copy()
    assert (len(base), int(base.outcome.eq("target_first").sum())) == (318, 198)
    dates_frame = pd.read_csv(DATA / "research_dates.csv")
    dates_frame["half"] = dates_frame.date.map(
        lambda d: f"{d[:4]}_H{(int(d[5:7]) - 1) // 6 + 1}"
    )
    old_summary = pd.read_csv(SOURCE / "summary.csv")
    summaries, changes, executions, overlaps, novelty, leaveout = [], [], [], [], [], []
    for period in ["pooled", *HALVES]:
        dates = dates_frame.loc[
            dates_frame.half.eq(period)
            if period != "pooled"
            else dates_frame.date.notna(),
            "date",
        ].tolist()
        part = events[events.date.isin(dates)]
        pb, pa = part[part.baseline], part[part.added]
        draws = np.random.default_rng(20260920).multinomial(
            len(dates), np.repeat(1 / len(dates), len(dates)), size=5000
        )
        for policy in ["all", "first", "spaced60"]:
            reference, union = thin(pb, policy), thin(part, policy)
            for label, frame in [("baseline", reference), ("combined", union)]:
                summaries.append(
                    dict(
                        dataset=label,
                        period=period,
                        policy=policy,
                        **summary_row(frame, reference, dates, draws),
                    )
                )
                if period == "pooled":
                    executions.append(frame.assign(dataset=label, policy=policy))
            inc, displaced = difference(union, reference), difference(reference, union)
            changes.append(
                dict(
                    period=period,
                    policy=policy,
                    newly_kept=len(inc),
                    newly_kept_wins=int(inc.outcome.eq("target_first").sum()),
                    displaced=len(displaced),
                    displaced_wins=int(displaced.outcome.eq("target_first").sum()),
                    net_n=len(union) - len(reference),
                    net_wins=int(
                        union.outcome.eq("target_first").sum()
                        - reference.outcome.eq("target_first").sum()
                    ),
                    new_active_dates=len(set(union.date) - set(reference.date)),
                )
            )
            if period == "pooled":
                executions.extend(
                    [
                        inc.assign(dataset="newly_kept", policy=policy),
                        displaced.assign(dataset="displaced", policy=policy),
                    ]
                )
            for label, flag in [
                ("baseline", "baseline"),
                ("b05_union", "b05_candidate"),
                ("persistence_union", "persistence_candidate"),
                ("b07_union", "b07_candidate"),
            ]:
                old = old_summary.query(
                    "dataset == @label and period == @period and policy == @policy"
                ).iloc[0]
                comparison = thin(part[part.baseline | part[flag]], policy)
                for col, val in describe(comparison).items():
                    np.testing.assert_allclose(
                        val, old[col], atol=1e-10, equal_nan=True
                    )
        summaries.append(
            dict(
                dataset="added_only",
                period=period,
                policy="all",
                **summary_row(pa, pb, dates, draws),
            )
        )
        for label, frame in [("baseline", pb), ("combined", part)]:
            counts = daily(frame, dates)
            n, wins = len(frame), int(frame.outcome.eq("target_first").sum())
            for date, row in counts.iterrows():
                leaveout.append(
                    dict(
                        dataset=label,
                        period=period,
                        removed_date=date,
                        removed_n=int(row.n),
                        removed_wins=int(row.wins),
                        remaining_n=n - int(row.n),
                        remaining_wins=wins - int(row.wins),
                        rate=100 * (wins - row.wins) / (n - row.n)
                        if n > row.n
                        else np.nan,
                    )
                )
        for pattern, group in pa.groupby("route_pattern"):
            overlaps.append(dict(period=period, pattern=pattern, **describe(group)))
        active = set(pb.date)
        for label, group in [
            ("existing_base_date", pa[pa.date.isin(active)]),
            ("new_date", pa[~pa.date.isin(active)]),
        ]:
            novelty.append(dict(period=period, date_group=label, **describe(group)))
    assert keys(base).issubset(keys(events)) and keys(base).isdisjoint(keys(added))
    tables = {
        "summary.csv": pd.DataFrame(summaries),
        "policy_changes.csv": pd.DataFrame(changes),
        "added_route_patterns.csv": pd.DataFrame(overlaps),
        "novel_dates.csv": pd.DataFrame(novelty),
        "leave_one_day_out.csv": pd.DataFrame(leaveout),
    }
    for name, table in tables.items():
        table.to_csv(DATA / name, index=False)
    events.to_parquet(DATA / "events.parquet", index=False)
    pd.concat(executions, ignore_index=True).to_parquet(
        DATA / "policy_executions.parquet", index=False
    )
    files = [DATA / n for n in [*tables, "events.parquet", "policy_executions.parquet"]]
    write_json(
        DATA / "analysis_receipt.json",
        dict(
            freeze_sha256=digest(DATA / "freeze.json"),
            code_sha256=digest(Path(__file__)),
            outputs={str(p): digest(p) for p in files},
            bootstrap_draws=5000,
            bootstrap_seed=20260920,
            component_summary_rows_reconciled=60,
        ),
    )
    print(
        tables["summary.csv"]
        .query("policy == 'all'")[
            [
                "dataset",
                "period",
                "n",
                "target_first",
                "rate",
                "days",
                "low",
                "high",
                "delta_vs_reference_pp",
                "delta_low",
                "delta_high",
            ]
        ]
        .to_string(index=False)
    )
    print(
        tables["policy_changes.csv"].query("period == 'pooled'").to_string(index=False)
    )
    print(
        tables["added_route_patterns.csv"]
        .query("period == 'pooled'")
        .to_string(index=False)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    prepare() if parser.parse_args().prepare else run()
