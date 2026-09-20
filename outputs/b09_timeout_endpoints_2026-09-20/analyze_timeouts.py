"""Describe fixed neither-barrier cases using native hour-end prices."""

import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = Path(__file__).resolve().parent
ROOT = Path("/Users/dgrissen/Dev/central_trade_data/thetadata")
SOURCE = ROOT / "b09_combined_expansion_2026-09-20-v1"
OLD = ROOT / "b09_or_path_distributions_2026-09-20-v1"
DATA = ROOT / "b09_timeout_endpoints_2026-09-20-v1"
HELPER = OUT.parent / "b09_or_path_distributions_2026-09-20/analyze.py"
SPEC = importlib.util.spec_from_file_location("existing_path_measurements", HELPER)
previous = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(previous)
COHORTS = {
    "B09 F4 OR SPX": "baseline",
    "B05 F4 alone": "b05_candidate",
    "B09 five-minute IV persistence": "persistence_candidate",
    "B07 original six-sector acceleration": "b07_candidate",
    "All combined": None,
}
EDGES = np.array([-10.0, -7.5, -5.0, -2.5, 0.0, 2.5, 5.0])
EPS = 1e-8


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(frame: pd.DataFrame) -> str:
    lines = ["| " + " | ".join(frame.columns) + " |", "|" + "---|" * len(frame.columns)]
    for row in frame.itertuples(index=False, name=None):
        cells = [
            "—" if pd.isna(v) else f"{v:.2f}" if isinstance(v, float) else str(v)
            for v in row
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    if DATA.exists() and any(DATA.iterdir()):
        raise FileExistsError("Preserve existing endpoint namespace")
    hashes = {}
    receipt = json.loads((SOURCE / "analysis_receipt.json").read_text())
    freeze = json.loads((SOURCE / "freeze.json").read_text())
    old_receipt = json.loads((OLD / "receipt.json").read_text())
    expectations = receipt["outputs"] | freeze["outputs"] | old_receipt["outputs"]
    for path in [
        SOURCE / "events.parquet",
        SOURCE / "research_dates.csv",
        OLD / "event_metrics.parquet",
    ]:
        assert sha(path) == expectations[str(path)], path
        hashes[str(path)] = sha(path)
    for path in [
        SOURCE / "analysis_receipt.json",
        SOURCE / "freeze.json",
        OLD / "receipt.json",
    ]:
        hashes[str(path)] = sha(path)
    all_events = pd.read_parquet(SOURCE / "events.parquet")
    calendar = pd.read_csv(SOURCE / "research_dates.csv", float_precision="round_trip")
    selected = all_events[all_events.outcome.eq("neither")].copy()
    assert len(selected) == 92 and not selected.duplicated(["date", "known_min"]).any()
    date_lookup = calendar.set_index("date")
    records, paths = [], []
    for date, group in selected.groupby("date"):
        meta = date_lookup.loc[date]
        path = Path(meta.source_path)
        assert sha(path) == meta.source_sha256
        hashes[str(path)] = sha(path)
        raw = pd.read_parquet(path)
        indexed = raw.set_index("min")
        assert not indexed.index.duplicated().any()
        for row in group.itertuples(index=False):
            metrics = previous.measure_path(raw, row.known_min)
            assert metrics["reproduced_outcome"] == "neither"
            assert metrics["reproduced_entry_price"] == row.entry_price
            start = row.known_min
            assert set(range(570, start + 60)).issubset(indexed.index)
            assert indexed.loc[570 : start - 1, "low"].gt(meta.vol_trigger).all()
            assert row.entry_price > meta.vol_trigger
            window = indexed.loc[list(range(start, start + 60))]
            # Separate direct no-touch and endpoint checks against native rows.
            assert window.high.max() < row.entry_price + 5 - EPS
            assert window.low.min() > row.entry_price - 10 + EPS
            delta = float(indexed.loc[start + 59, "close"] - indexed.loc[start, "open"])
            assert abs(delta - metrics["final_move_points"]) < EPS and -10 < delta < 5
            records.append(
                row._asdict()
                | {
                    "final_close": metrics["final_close"],
                    "final_move_points": delta,
                    "final_bar_start_min": start + 59,
                    "horizon_end_min": start + 60,
                    "horizon_end_timestamp_et": previous.timestamp(date, start + 60),
                    "hour_min_low": float(window.low.min()),
                    "hour_max_high": float(window.high.max()),
                    "native_source_path": str(path),
                    "native_source_sha256": meta.source_sha256,
                }
            )
            paths.append(
                window.reset_index()[["min", "open", "high", "low", "close"]].assign(
                    date=date, known_min=start
                )
            )
    events = pd.DataFrame(records).sort_values(["date", "known_min"])
    prior = pd.read_parquet(OLD / "event_metrics.parquet")
    before = (
        prior[prior.outcome.eq("neither")]
        .set_index(["date", "known_min"])
        .final_move_points.sort_index()
    )
    now = (
        events[events.baseline]
        .set_index(["date", "known_min"])
        .final_move_points.sort_index()
    )
    pd.testing.assert_series_equal(before, now)
    rows, bins, empirical = [], [], []
    for cohort, flag in COHORTS.items():
        original = all_events[all_events[flag]] if flag else all_events
        members = events[events[flag]] if flag else events
        for period in ["pooled", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]:
            base = (
                original if period == "pooled" else original[original.half.eq(period)]
            )
            group = members if period == "pooled" else members[members.half.eq(period)]
            values = group.final_move_points.to_numpy()
            assert len(group) == int(base.outcome.eq("neither").sum())
            stats = previous.summarize_values(values)
            row = dict(
                cohort=cohort,
                period=period,
                total_signals=len(base),
                n=len(group),
                timeout_percent=100 * len(group) / len(base) if len(base) else np.nan,
                active_dates=group.date.nunique(),
                **stats,
                negative=int((values < -EPS).sum()),
                flat=int((np.abs(values) <= EPS).sum()),
                positive=int((values > EPS).sum()),
                positive_percent=100 * (values > EPS).sum() / len(values)
                if len(values)
                else np.nan,
            )
            assert row["negative"] + row["flat"] + row["positive"] == len(values)
            if len(values):
                ordered = sorted(values)
                for q, name in [
                    (0.1, "p10"),
                    (0.25, "p25"),
                    (0.5, "median"),
                    (0.75, "p75"),
                    (0.9, "p90"),
                ]:
                    pos = q * (len(ordered) - 1)
                    lower, upper = int(np.floor(pos)), int(np.ceil(pos))
                    manual = ordered[lower] + (pos - lower) * (
                        ordered[upper] - ordered[lower]
                    )
                    assert abs(manual - stats[name]) < EPS
                assert abs(sum(values) / len(values) - stats["mean"]) < EPS
            rows.append(row)
            counts, _ = np.histogram(values, bins=EDGES)
            assert counts.sum() == len(values)
            for i, count in enumerate(counts):
                manual = sum(EDGES[i] <= value < EDGES[i + 1] for value in values)
                assert manual == count
                bins.append(
                    dict(
                        cohort=cohort,
                        period=period,
                        lower=EDGES[i],
                        upper=EDGES[i + 1],
                        n=int(count),
                        percent=100 * count / len(values) if len(values) else np.nan,
                    )
                )
            if period == "pooled":
                for rank, value in enumerate(sorted(values), 1):
                    empirical.append(
                        dict(
                            cohort=cohort,
                            rank=rank,
                            n=len(values),
                            final_move_points=value,
                            cumulative_percent=100 * rank / len(values),
                        )
                    )
    summary, hist = pd.DataFrame(rows), pd.DataFrame(bins)
    DATA.mkdir()
    events.to_parquet(DATA / "events.parquet", index=False)
    events.to_csv(DATA / "events.csv", index=False)
    pd.concat(paths, ignore_index=True).to_parquet(
        DATA / "minute_paths.parquet", index=False
    )
    summary.to_csv(DATA / "summary.csv", index=False)
    hist.to_csv(DATA / "histogram_bins.csv", index=False)
    pd.DataFrame(empirical).to_csv(DATA / "empirical_distribution.csv", index=False)
    fig, axes = plt.subplots(
        5, 1, figsize=(10.8, 10.8), sharex=True, layout="constrained"
    )
    for ax, (cohort, flag) in zip(axes, COHORTS.items(), strict=True):
        group = events[events[flag]] if flag else events
        values = group.final_move_points.to_numpy()
        ax.hist(
            values,
            bins=EDGES,
            weights=np.full(len(values), 100 / len(values)),
            color="#3977a8",
            edgecolor="white",
            linewidth=1.5,
        )
        ax.axvline(0, color="#333333", linewidth=1)
        ax.axvline(np.median(values), color="#cc751e", linewidth=2, linestyle="--")
        ax.set_title(
            f"{cohort}  |  N={len(values)}  |  median {np.median(values):+.2f}",
            loc="left",
            fontsize=11,
        )
        ax.set_ylim(0, 65)
        ax.set_ylabel("% of entries")
        ax.spines[["top", "right"]].set_visible(False)
    axes[-1].set_xticks(EDGES)
    axes[-1].set_xlabel("SPX points at the end of 60 minutes, relative to entry")
    fig.suptitle(
        "Neither +5 nor −10 touched during the hour\nUnspaced entries; dashed orange line = sample median",
        fontsize=14,
    )
    fig.savefig(OUT / "endpoint_distributions.png", dpi=160)
    plt.close(fig)
    columns = [
        "cohort",
        "period",
        "total_signals",
        "n",
        "timeout_percent",
        "active_dates",
        "negative",
        "flat",
        "positive",
        "positive_percent",
        "min",
        "p10",
        "p25",
        "median",
        "p75",
        "p90",
        "max",
        "mean",
    ]
    (OUT / "ALL_RESULTS.md").write_text(
        "# End-of-hour neither-barrier distributions\n\nAll values in SPX points unless labeled percent. Quantiles are sample distribution summaries, not confidence intervals.\n\n"
        + table(summary[columns])
        + "\n\n## Fixed histogram bins\n\n"
        + table(hist)
        + "\n"
    )
    # Recheck sources after analysis and record all generated table hashes.
    for path, expected in hashes.items():
        assert sha(Path(path)) == expected, path
    outputs = {str(p): sha(p) for p in DATA.iterdir() if p.is_file()}
    outputs.update(
        {
            str(OUT / n): sha(OUT / n)
            for n in ["ALL_RESULTS.md", "endpoint_distributions.png"]
        }
    )
    record = dict(
        inputs=hashes,
        code_protocol={
            str(p): sha(p) for p in [Path(__file__), OUT / "PROTOCOL.md", HELPER]
        },
        outputs=outputs,
        provider_calls=0,
        verification=dict(
            unique_native_paths=92,
            minute_rows=5520,
            baseline_prior_endpoints=43,
            summary_rows=25,
            histogram_rows=150,
            all_sources_unchanged=True,
        ),
        endpoint="close of native bar T+59 minus open(T); close boundary T+60",
        independent_review=False,
    )
    (DATA / "receipt.json").write_text(json.dumps(record, indent=2) + "\n")
    print(summary[summary.period.eq("pooled")][columns].to_string(index=False))


if __name__ == "__main__":
    main()
