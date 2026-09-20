"""Fixed outcome tables with day-cluster intervals, then day-removal sensitivity."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = Path("/Users/dgrissen/Dev/central_trade_data/thetadata")
SOURCE = ROOT / "b09_combined_expansion_2026-09-20-v1"
ENDPOINTS = ROOT / "b09_timeout_endpoints_2026-09-20-v1"
DATA = ROOT / "b09_outcome_stability_2026-09-20-v1"
PERSONA = Path(
    "/Users/dgrissen/.config/persona-review-kit/personas/market/charlie-mcelligott.md"
)
PERIODS = ["2025_H1", "2025_H2", "2026_H1", "2026_H2", "pooled"]
CATEGORIES = [
    "wins",
    "stops",
    "neg10_7_5",
    "neg7_5_5",
    "neg5_2_5",
    "neg2_5_0",
    "flat",
    "pos0_2_5",
    "pos2_5_5",
]
EPS = 1e-8


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def classify(outcome: str, endpoint: float) -> str:
    """Partition first-touch outcomes, using endpoints only for neither cases."""
    if outcome == "target_first":
        return "wins"
    if outcome == "adverse_first":
        return "stops"
    if outcome != "neither" or not math.isfinite(endpoint) or not -10 < endpoint < 5:
        raise ValueError("Invalid unresolved endpoint/outcome")
    if abs(endpoint) <= EPS:
        return "flat"
    for upper, name in [
        (-7.5, "neg10_7_5"),
        (-5.0, "neg7_5_5"),
        (-2.5, "neg5_2_5"),
        (0.0, "neg2_5_0"),
        (2.5, "pos0_2_5"),
        (5.0, "pos2_5_5"),
    ]:
        if endpoint < upper:
            return name
    raise ValueError("Unclassified endpoint")


def daily(frame: pd.DataFrame, dates: list[str]) -> pd.DataFrame:
    return pd.crosstab(frame.date, frame.category).reindex(
        index=dates, columns=CATEGORIES, fill_value=0
    )


def day_deletions(frame: pd.DataFrame, dates: list[str]) -> pd.DataFrame:
    """Remove every entry on one date and recalculate the remaining outcome mix."""
    days = daily(frame, dates)
    total = days.sum()
    rows = []
    for date, removed in days.iterrows():
        remaining = total - removed
        n = int(remaining.sum())
        rows.append(
            dict(
                removed_date=date,
                removed_n=int(removed.sum()),
                removed_wins=int(removed.wins),
                removed_stops=int(removed.stops),
                remaining_n=n,
                **{c: int(remaining[c]) for c in CATEGORIES},
                **{
                    c + "_pct": 100 * remaining[c] / n if n else np.nan
                    for c in CATEGORIES
                },
            )
        )
    return pd.DataFrame(rows)


def groups(events: pd.DataFrame, calendar: pd.DataFrame):
    for period in PERIODS:
        dates = calendar.loc[
            calendar.half.eq(period) if period != "pooled" else calendar.date.notna(),
            "date",
        ].tolist()
        part = events[events.date.isin(dates)]
        yield period, dates, {"baseline": part[part.baseline], "combined": part}


def render_ci_table(table: pd.DataFrame) -> str:
    parts = [
        "# Outcome tables with winner-rate 95% confidence intervals\n\nAll percentages use all signals in the row. Endpoint buckets include only neither-barrier cases. No spacing. Confidence intervals use whole-date resampling, not independent-signal trials.\n"
    ]
    for dataset in ["baseline", "combined"]:
        parts.append(
            f"\n## {dataset.capitalize()}\n\n| Half | Winners/signals | Win % | 95% CI | Stop % | −7.5 to <−5 | −5 to <−2.5 | −2.5 to <0 | Flat | >0 to <+2.5 | +2.5 to <+5 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )
        for r in table[table.dataset.eq(dataset)].itertuples():
            cells = [
                r.period,
                f"{r.wins}/{r.n}",
                f"{r.wins_pct:.1f}%",
                f"{r.low:.1f}–{r.high:.1f}%",
            ]
            cells += [
                f"{getattr(r, c + '_pct'):.1f}%"
                for c in [
                    "stops",
                    "neg7_5_5",
                    "neg5_2_5",
                    "neg2_5_0",
                    "flat",
                    "pos0_2_5",
                    "pos2_5_5",
                ]
            ]
            parts.append("| " + " | ".join(cells) + " |\n")
    parts.append(
        "\nNo unresolved entry ends between −10 and −7.5, so that zero column is omitted. 2026_H2 is partial through September18; pooled is the total. Percentages may not sum exactly to100 after rounding.\n\nIntervals use5000whole-date resamples,seed20260920. Baseline2026H2 has4999finite replicates and one zero-signal replicate, omitted; every other row has5000. These intervals do not adjust for earlier searches or between-date dependence.\n"
    )
    return "".join(parts)


def confidence_phase() -> None:
    """Publish full-sample intervals before running the follow-up deletion phase."""
    if DATA.exists() and any(DATA.iterdir()):
        raise FileExistsError("CI namespace already exists")
    receipts = [
        json.loads((SOURCE / "analysis_receipt.json").read_text()),
        json.loads((SOURCE / "freeze.json").read_text()),
        json.loads((ENDPOINTS / "receipt.json").read_text()),
    ]
    expected = {}
    for receipt in receipts:
        expected.update(receipt["outputs"])
    inputs = {}
    paths = [
        SOURCE / "events.parquet",
        SOURCE / "summary.csv",
        SOURCE / "leave_one_day_out.csv",
        SOURCE / "research_dates.csv",
        ENDPOINTS / "events.parquet",
    ]
    for p in paths:
        assert digest(p) == expected[str(p)], p
        inputs[str(p)] = digest(p)
    source = pd.read_parquet(SOURCE / "events.parquet")
    endpoint = pd.read_parquet(ENDPOINTS / "events.parquet")
    events = source.merge(
        endpoint[["date", "known_min", "final_move_points"]],
        on=["date", "known_min"],
        how="left",
        validate="one_to_one",
    )
    assert (
        len(events) == 685
        and events.final_move_points.notna().eq(events.outcome.eq("neither")).all()
    )
    events["category"] = [
        classify(r.outcome, r.final_move_points) for r in events.itertuples()
    ]
    calendar = pd.read_csv(SOURCE / "research_dates.csv")
    calendar["half"] = calendar.date.map(
        lambda d: f"{d[:4]}_H{1 + (int(d[5:7]) - 1) // 6}"
    )
    reference = pd.read_csv(SOURCE / "summary.csv").query("policy == 'all'")
    rows, deltas = [], []
    for period, dates, cohorts in groups(events, calendar):
        draws = np.random.default_rng(20260920).multinomial(
            len(dates), np.repeat(1 / len(dates), len(dates)), size=5000
        )
        rates = {}
        for dataset, frame in cohorts.items():
            day = daily(frame, dates)
            totals = day.sum()
            n = int(totals.sum())
            bn, bw = draws @ day.sum(axis=1).to_numpy(), draws @ day.wins.to_numpy()
            rate = np.divide(100.0 * bw, bn, out=np.full(len(bn), np.nan), where=bn > 0)
            finite = rate[np.isfinite(rate)]
            low, high = np.quantile(finite, [0.025, 0.975])
            old = reference.query("dataset == @dataset and period == @period").iloc[0]
            np.testing.assert_allclose(
                [totals.wins, n, 100 * totals.wins / n, low, high],
                [old.target_first, old.n, old.rate, old.low, old.high],
                atol=1e-10,
            )
            assert len(finite) == old.finite_draws
            rows.append(
                dict(
                    dataset=dataset,
                    period=period,
                    n=n,
                    active_dates=frame.date.nunique(),
                    research_dates=len(dates),
                    low=float(low),
                    high=float(high),
                    finite_draws=len(finite),
                    **{c: int(totals[c]) for c in CATEGORIES},
                    **{c + "_pct": 100 * totals[c] / n for c in CATEGORIES},
                )
            )
            rates[dataset] = rate
        delta = rates["combined"] - rates["baseline"]
        finite = delta[np.isfinite(delta)]
        low, high = np.quantile(finite, [0.025, 0.975])
        old = reference.query("dataset == 'combined' and period == @period").iloc[0]
        np.testing.assert_allclose(
            [low, high], [old.delta_low, old.delta_high], atol=1e-10
        )
        deltas.append(
            dict(
                period=period,
                change_pp=float(old.delta_vs_reference_pp),
                low=float(low),
                high=float(high),
                finite_draws=len(finite),
            )
        )
    table = pd.DataFrame(rows)
    assert np.allclose(table[[c + "_pct" for c in CATEGORIES]].sum(axis=1), 100)
    DATA.mkdir()
    events.to_parquet(DATA / "classified_events.parquet", index=False)
    calendar.to_csv(DATA / "research_dates.csv", index=False)
    table.to_csv(DATA / "table_with_ci.csv", index=False)
    pd.DataFrame(deltas).to_csv(DATA / "paired_ci.csv", index=False)
    (OUT / "TABLES_WITH_CI.md").write_text(render_ci_table(table))
    files = [
        DATA / n
        for n in [
            "classified_events.parquet",
            "research_dates.csv",
            "table_with_ci.csv",
            "paired_ci.csv",
        ]
    ] + [OUT / "TABLES_WITH_CI.md"]
    write_json(
        DATA / "ci_receipt.json",
        dict(
            inputs=inputs,
            outputs={str(p): digest(p) for p in files},
            code_protocol={
                str(p): digest(p)
                for p in [Path(__file__), OUT / "PROTOCOL.md", PERSONA]
            },
            phase="confidence_intervals_before_new_day_deletion",
            matched_prior_interval_rows=10,
            draws=5000,
            seed=20260920,
        ),
    )
    print(
        table[["dataset", "period", "wins", "n", "wins_pct", "low", "high"]].to_string(
            index=False
        )
    )


def deletion_phase() -> None:
    """Recount all categories after removing a session; do not refit any rule."""
    ci = json.loads((DATA / "ci_receipt.json").read_text())
    for hashes in [ci["inputs"], ci["outputs"], ci["code_protocol"]]:
        for p, h in hashes.items():
            assert digest(Path(p)) == h, p
    charlie = OUT / "CHARLIE_INTERPRETATION.md"
    assert charlie.is_file(), (
        "Write the local Charlie interpretation after CI and before deletion"
    )
    events = pd.read_parquet(DATA / "classified_events.parquet")
    calendar = pd.read_csv(DATA / "research_dates.csv")
    old = pd.read_csv(SOURCE / "leave_one_day_out.csv").set_index(
        ["dataset", "period", "removed_date"]
    )
    full, summary, paired = [], [], []
    for period, dates, cohorts in groups(events, calendar):
        per = {}
        for dataset, frame in cohorts.items():
            deletion = day_deletions(frame, dates)
            day = daily(frame, dates)
            for r in deletion.itertuples():
                kept = frame[frame.date.ne(r.removed_date)]
                counts = kept.category.value_counts()
                assert len(kept) == r.remaining_n
                for cat in CATEGORIES:
                    assert int(counts.get(cat, 0)) == getattr(r, cat)
                prior = old.loc[(dataset, period, r.removed_date)]
                assert (r.remaining_n, r.wins) == (
                    prior.remaining_n,
                    prior.remaining_wins,
                )
                np.testing.assert_allclose(
                    r.wins_pct, prior.rate, atol=1e-10, equal_nan=True
                )
            active = deletion[deletion.removed_n.gt(0)]
            worst = active.sort_values(["wins_pct", "removed_date"]).iloc[0]
            best = active.sort_values(
                ["wins_pct", "removed_date"], ascending=[False, True]
            ).iloc[0]
            largest = day.sort_values(["wins"], ascending=False, kind="stable").iloc[0]
            largest_date = day.sort_values(
                ["wins"], ascending=False, kind="stable"
            ).index[0]
            rates = {
                f"{c}_min_pct": float(active[c + "_pct"].min()) for c in CATEGORIES
            }
            rates.update(
                {f"{c}_max_pct": float(active[c + "_pct"].max()) for c in CATEGORIES}
            )
            n = len(frame)
            wins = int(frame.category.eq("wins").sum())
            summary.append(
                dict(
                    dataset=dataset,
                    period=period,
                    n=n,
                    wins=wins,
                    original_rate=100 * wins / n,
                    active_dates=len(active),
                    research_dates=len(dates),
                    worst_removed_date=worst.removed_date,
                    worst_removed_n=int(worst.removed_n),
                    worst_removed_wins=int(worst.removed_wins),
                    worst_remaining_n=int(worst.remaining_n),
                    worst_remaining_wins=int(worst.wins),
                    best_removed_date=best.removed_date,
                    largest_winner_date=largest_date,
                    largest_day_wins=int(largest.wins),
                    largest_day_n=int(largest.sum()),
                    top5_wins=int(day.wins.nlargest(5).sum()),
                    top5_winner_share_pct=100 * day.wins.nlargest(5).sum() / wins,
                    **rates,
                )
            )
            deletion["dataset"], deletion["period"] = dataset, period
            per[dataset] = deletion.set_index("removed_date")
            full.append(deletion)
        for date in dates:
            b, c = per["baseline"].loc[date], per["combined"].loc[date]
            paired.append(
                dict(
                    period=period,
                    removed_date=date,
                    baseline_n=int(b.remaining_n),
                    combined_n=int(c.remaining_n),
                    baseline_rate=b.wins_pct,
                    combined_rate=c.wins_pct,
                    change_pp=c.wins_pct - b.wins_pct,
                )
            )
    results = {
        "leave_one_day_out.csv": pd.concat(full, ignore_index=True),
        "stability_summary.csv": pd.DataFrame(summary),
        "paired_day_deletions.csv": pd.DataFrame(paired),
    }
    assert len(results["leave_one_day_out.csv"]) == 956
    for name, frame in results.items():
        frame.to_csv(DATA / name, index=False)
    write_json(
        DATA / "deletion_receipt.json",
        dict(
            ci_receipt_sha256=digest(DATA / "ci_receipt.json"),
            charlie_interpretation_sha256=digest(charlie),
            outputs={str(DATA / n): digest(DATA / n) for n in results},
            verified_rows=956,
            category_recounts=956 * len(CATEGORIES),
            paired_rows=len(paired),
            independent_reviewer=False,
            provider_calls=0,
        ),
    )
    print(
        results["stability_summary.csv"][
            [
                "dataset",
                "period",
                "original_rate",
                "wins_min_pct",
                "wins_max_pct",
                "stops_min_pct",
                "stops_max_pct",
                "worst_removed_date",
                "worst_removed_wins",
                "worst_removed_n",
                "worst_remaining_wins",
                "worst_remaining_n",
                "top5_winner_share_pct",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["ci", "delete"])
    confidence_phase() if parser.parse_args().phase == "ci" else deletion_phase()
