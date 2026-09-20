"""Extend the fixed cached-volume diagnostic to the five frozen cohorts."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
PREVIOUS_CODE = OUT.parent / "b09_opportunity_expansion_2026-09-20"
sys.path.insert(0, str(PREVIOUS_CODE))
from analyze import summary_row, volume_controls  # noqa: E402
from prepare import volume_features  # noqa: E402
from study import HALVES, SPY, describe, digest, write_json  # noqa: E402

ROOT = Path("/Users/dgrissen/Dev/central_trade_data/thetadata")
SOURCE = ROOT / "b09_combined_expansion_2026-09-20-v1"
OLD = ROOT / "b09_opportunity_expansion_2026-09-20-v1"
DATA = ROOT / "b09_working_set_volume_2026-09-20-v1"
FLAGS = {
    "B09_F4_OR_SPX": "baseline",
    "B05_F4": "b05_candidate",
    "B09_persistence": "persistence_candidate",
    "B07_original_six": "b07_candidate",
    "combined": None,
}
EXPECTED = [(318, 198), (112, 70), (492, 308), (91, 57), (685, 427)]


def checked(path: Path, expected: str, hashes: dict) -> None:
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"Changed source: {path}")
    hashes[str(path)] = actual


def prepare() -> None:
    """Freeze outcome-free features before their join to existing outcomes."""
    if (DATA / "freeze.json").exists():
        raise FileExistsError("Features are already frozen")
    DATA.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((SOURCE / "freeze.json").read_text())
    old = json.loads((OLD / "freeze.json").read_text())
    hashes = {}
    for name in ["memberships.parquet", "research_dates.csv"]:
        path = SOURCE / name
        checked(path, frozen["outputs"][str(path)], hashes)
    checked(SPY, old["inputs"][str(SPY)], hashes)
    old_features = OLD / "volume_features.parquet"
    checked(old_features, old["outputs"][str(old_features)], hashes)
    members = pd.read_parquet(SOURCE / "memberships.parquet")
    dates = pd.read_csv(SOURCE / "research_dates.csv")
    assert len(members) == 685 and len(dates) == 239
    assert not members.duplicated(["date", "known_min"]).any()
    members["entry_id"] = members.date + "|" + members.known_min.astype(str)
    features = volume_features(members, dates, hashes)
    assert len(features) == len(members)

    earlier = pd.read_parquet(old_features)
    overlap = features.merge(earlier, on=["date", "known_min"], suffixes=("", "_old"))
    for col in [
        "rvol",
        "reference_median",
        "current_volume",
        "return30_bps",
        "rv30_points",
    ]:
        np.testing.assert_allclose(
            overlap[col], overlap[col + "_old"], rtol=0, atol=0, equal_nan=True
        )
    for col in ["status", "state", "history_dates"]:
        assert overlap[col].equals(overlap[col + "_old"].rename(col))
    assert len(overlap) >= 492
    features.to_parquet(DATA / "features.parquet", index=False)
    members.to_parquet(DATA / "memberships.parquet", index=False)
    dates.to_csv(DATA / "research_dates.csv", index=False)
    write_json(
        DATA / "freeze.json",
        {
            "inputs": hashes,
            "code": {
                str(p): digest(p)
                for p in [
                    Path(__file__),
                    OUT / "PROTOCOL.md",
                    *[
                        PREVIOUS_CODE / n
                        for n in ["study.py", "prepare.py", "analyze.py"]
                    ],
                ]
            },
            "outputs": {
                str(DATA / n): digest(DATA / n)
                for n in [
                    "features.parquet",
                    "memberships.parquet",
                    "research_dates.csv",
                ]
            },
            "outcome_free": True,
            "earlier_feature_rows_exactly_reconciled": len(overlap),
            "scope": "Known outcome cohorts, no new holdout; fixed existing RVOL feature",
        },
    )
    print(
        "Frozen features",
        len(features),
        "old overlap",
        len(overlap),
        features.status.value_counts().to_dict(),
    )


def direct_feature_check(features: pd.DataFrame) -> None:
    """Independently use explicit five-column sums, not the rolling builder."""
    raw = pd.read_parquet(SPY, columns=["date", "min", "volume"])
    raw["date"] = raw.date.astype(str)
    calendar = sorted(raw.date.unique())
    raw = raw[raw["min"].between(570, 959)]
    matrix = raw.pivot(index="date", columns="min", values="volume").reindex(
        index=calendar, columns=range(570, 960)
    )
    values = matrix.to_numpy(dtype=float)
    positions = {d: i for i, d in enumerate(calendar)}
    for row in features.itertuples():
        position = positions.get(row.date)
        if position is None:
            assert row.status == "current_unavailable" and row.state == "unknown"
            continue
        assert position >= 60
        minutes = slice(row.known_min - 5 - 570, row.known_min - 570)
        current = values[position, minutes]
        history = values[position - 60 : position, minutes]
        assert history.shape == (60, 5)
        assert all(d < row.date for d in json.loads(row.history_dates))
        if not (np.isfinite(current).all() and (current >= 0).all()):
            assert row.status == "current_incomplete"
            continue
        np.testing.assert_equal(row.current_volume, current.sum())
        if not (np.isfinite(history).all() and (history >= 0).all()):
            assert row.status == "incomplete_history" and row.state == "unknown"
            continue
        reference = np.median(history.sum(axis=1))
        if reference <= 0:
            assert row.status == "nonpositive_reference"
            continue
        np.testing.assert_equal(row.reference_median, reference)
        np.testing.assert_equal(row.rvol, current.sum() / reference)
        assert row.status == "ok"
        assert row.state == ("yes" if row.rvol > 1 else "no")


def cohorts(events: pd.DataFrame):
    for (name, flag), (n, wins) in zip(FLAGS.items(), EXPECTED, strict=True):
        part = events if flag is None else events[events[flag]]
        assert (len(part), int(part.outcome.eq("target_first").sum())) == (n, wins)
        yield name, part


def states(part: pd.DataFrame) -> dict:
    return {
        "all": part,
        "observed": part[part.volume_state.ne("unknown")],
        "high": part[part.volume_state.eq("yes")],
        "ordinary": part[part.volume_state.eq("no")],
        "unknown": part[part.volume_state.eq("unknown")],
    }


def analyze() -> None:
    """Join immutable outcomes and score only the comparisons in the protocol."""
    if (DATA / "analysis_receipt.json").exists():
        raise FileExistsError("Analysis already recorded")
    freeze = json.loads((DATA / "freeze.json").read_text())
    for group in ["inputs", "outputs", "code"]:
        for path, expected in freeze[group].items():
            checked(Path(path), expected, {})
    features = pd.read_parquet(DATA / "features.parquet")
    direct_feature_check(features)
    receipt = json.loads((SOURCE / "analysis_receipt.json").read_text())
    source = SOURCE / "events.parquet"
    checked(source, receipt["outputs"][str(source)], {})
    events = pd.read_parquet(source).merge(
        features.drop(columns="entry_id"),
        on=["date", "known_min"],
        validate="one_to_one",
    )
    assert len(events) == 685
    events = events.rename(columns={"state": "volume_state"})
    events["block"] = (events.known_min - 1 - 570) // 60
    events.to_parquet(DATA / "events.parquet", index=False)
    dates = pd.read_csv(DATA / "research_dates.csv")
    dates["half"] = dates.date.str[:4] + np.where(
        dates.date.str[5:7].astype(int) <= 6, "_H1", "_H2"
    )
    summaries, coverage, controls, details, balances, deletions = [], [], [], [], [], []
    for period in [*HALVES, "pooled"]:
        calendar = (
            dates.date.tolist()
            if period == "pooled"
            else dates.loc[dates.half.eq(period), "date"].tolist()
        )
        rng = np.random.default_rng(20260920)
        draws = rng.multinomial(
            len(calendar), np.repeat(1 / len(calendar), len(calendar)), size=5000
        )
        for name, full in cohorts(events):
            part = full if period == "pooled" else full[full.half.eq(period)]
            subsets = states(part)
            assert len(subsets["observed"]) + len(subsets["unknown"]) == len(part)
            assert len(subsets["high"]) + len(subsets["ordinary"]) == len(
                subsets["observed"]
            )
            for state, frame in subsets.items():
                row = summary_row(frame, subsets["ordinary"], calendar, draws)
                observed = describe(subsets["observed"])
                gate = summary_row(frame, subsets["observed"], calendar, draws)
                row.update(
                    cohort=name,
                    period=period,
                    state=state,
                    delta_vs_observed_pp=gate["delta_vs_reference_pp"],
                    delta_vs_observed_low=gate["delta_low"],
                    delta_vs_observed_high=gate["delta_high"],
                    observed_n=observed["n"],
                    observed_wins=observed["target_first"],
                )
                summaries.append(row)
            for status, group in part.groupby("status"):
                coverage.append(
                    dict(cohort=name, period=period, status=status, **describe(group))
                )
            for state, group in part.groupby("volume_state"):
                balances.append(
                    dict(
                        cohort=name,
                        period=period,
                        state=state,
                        n=len(group),
                        return30_mean=group.return30_bps.mean(),
                        return30_median=group.return30_bps.median(),
                        rv30_mean=group.rv30_points.mean(),
                        rv30_median=group.rv30_points.median(),
                        rvol_median=group.rvol.median(),
                    )
                )
            if period != "pooled":
                continue
            # Reuse the prior block diagnostic's all_b09 calculation on this exact
            # cohort; discard its redundant baseline calculation, label explicitly.
            strata, summary, _ = volume_controls(part)
            strata = strata[strata.cohort.eq("all_b09")].assign(cohort=name)
            summary = summary[summary.cohort.eq("all_b09")].assign(cohort=name)
            details.append(strata)
            controls.append(summary)
            for date in calendar:
                retained = states(part[part.date.ne(date)])
                high, ordinary = (
                    describe(retained["high"]),
                    describe(retained["ordinary"]),
                )
                deletions.append(
                    dict(
                        cohort=name,
                        removed_date=date,
                        high_n=high["n"],
                        high_wins=high["target_first"],
                        ordinary_n=ordinary["n"],
                        ordinary_wins=ordinary["target_first"],
                        delta_pp=high["rate"] - ordinary["rate"],
                    )
                )
    pd.DataFrame(summaries).to_csv(DATA / "summary.csv", index=False)
    pd.DataFrame(coverage).to_csv(DATA / "coverage.csv", index=False)
    pd.DataFrame(balances).to_csv(DATA / "context_balance.csv", index=False)
    pd.concat(controls, ignore_index=True).to_csv(
        DATA / "within_block.csv", index=False
    )
    pd.concat(details, ignore_index=True).to_csv(
        DATA / "block_details.csv", index=False
    )
    pd.DataFrame(deletions).to_csv(DATA / "leave_one_date_out.csv", index=False)
    events[events.volume_state.eq("unknown")].to_csv(
        DATA / "unknown_entries.csv", index=False
    )
    # Exactly reproduce the earlier baseline table, including unknowns.
    base = events[events.baseline]
    assert {
        k: (len(v), int(v.outcome.eq("target_first").sum()))
        for k, v in states(base).items()
    } == {
        "all": (318, 198),
        "observed": (284, 176),
        "high": (136, 84),
        "ordinary": (148, 92),
        "unknown": (34, 22),
    }
    write_json(
        DATA / "analysis_receipt.json",
        {
            "freeze_sha256": digest(DATA / "freeze.json"),
            "outcomes_sha256": digest(source),
            "code_sha256": digest(Path(__file__)),
            "feature_rows_directly_verified": len(features),
            "prior_feature_overlap": freeze["earlier_feature_rows_exactly_reconciled"],
            "prior_baseline_counts_exact": True,
            "bootstrap_draws": 5000,
            "bootstrap_seed": 20260920,
            "outputs": {
                str(p): digest(p)
                for p in DATA.iterdir()
                if p.suffix in [".csv", ".parquet"]
            },
        },
    )
    print(
        pd.DataFrame(summaries)
        .query("period == 'pooled'")[
            [
                "cohort",
                "state",
                "n",
                "target_first",
                "rate",
                "delta_vs_reference_pp",
                "delta_low",
                "delta_high",
            ]
        ]
        .to_string(index=False)
    )
    print(pd.concat(controls).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "analyze"])
    args = parser.parse_args()
    (prepare if args.phase == "prepare" else analyze)()
