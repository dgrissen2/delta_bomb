"""Independently replay combined membership, native outcomes and accounting."""

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from combined import DATA, FLAGS, OUT, SOURCE, digest, write_json


def policy(rows: dict, name: str) -> dict:
    """Scalar chronological implementation, independent of the scoring helper."""
    result, last = {}, {}
    for (date, minute), row in sorted(rows.items()):
        if (
            name == "all"
            or date not in last
            or (name == "spaced60" and minute >= last[date] + 60)
        ):
            result[date, minute] = row
            last[date] = minute
    return result


def check_counts(rows: dict, result: object) -> None:
    counts = Counter(r.outcome for r in rows.values())
    assert len(rows) == result.n
    assert len({d for d, _ in rows}) == result.days
    for name in ["target_first", "adverse_first", "neither", "ambiguous"]:
        assert counts[name] == getattr(result, name)
    rate = 100 * counts["target_first"] / len(rows) if rows else np.nan
    np.testing.assert_allclose(rate, result.rate, atol=1e-10, equal_nan=True)


def main() -> None:
    freeze = json.loads((DATA / "freeze.json").read_text())
    receipt = json.loads((DATA / "analysis_receipt.json").read_text())
    for hashes in [
        freeze["inputs"],
        freeze["code_protocol"],
        freeze["outputs"],
        receipt["outputs"],
    ]:
        for path, expected in hashes.items():
            assert digest(Path(path)) == expected, path
    assert digest(DATA / "freeze.json") == receipt["freeze_sha256"]
    parents = pd.read_parquet(SOURCE / "memberships.parquet")
    expected = {}
    for row in parents.itertuples():
        admitted = [bool(getattr(row, c)) for c in FLAGS]
        if any(admitted):
            current = expected.setdefault((row.date, row.known_min), [False] * 4)
            for i, v in enumerate(admitted):
                current[i] = current[i] or v
    frame = pd.read_parquet(DATA / "events.parquet")
    rows = {(r.date, r.known_min): r for r in frame.itertuples()}
    assert len(rows) == len(frame) and set(rows) == set(expected)
    for key, flags in expected.items():
        row = rows[key]
        assert [getattr(row, c) for c in FLAGS] == flags
        assert row.added == (not flags[0])
        assert row.route_pattern == "+".join(
            n
            for n, yes in zip(["B05", "B09_persistence", "B07"], flags[1:], strict=True)
            if yes
        )
    calendar = pd.read_csv(DATA / "research_dates.csv", float_precision="round_trip")
    assert len(calendar) == calendar.date.nunique() == 239
    native_count = 0
    for date in calendar.itertuples():
        assert digest(Path(date.source_path)) == date.source_sha256
        selected = [r for (d, _), r in rows.items() if d == date.date]
        if not selected:
            continue
        price = pd.read_parquet(date.source_path).set_index("min")
        assert not price.index.duplicated().any()
        for row in selected:
            start = row.known_min
            assert set(range(570, start + 60)).issubset(set(price.index))
            entry = price.loc[start, "open"]
            assert entry == row.entry_price and entry > date.vol_trigger
            assert price.loc[570 : start - 1, "low"].gt(date.vol_trigger).all()
            label, touch = "neither", np.nan
            for minute in range(start, start + 60):
                bar = price.loc[minute]
                up = bar.high >= entry + 5 - 1e-8
                down = bar.low <= entry - 10 + 1e-8
                if up or down:
                    label = (
                        "ambiguous"
                        if up and down
                        else "target_first"
                        if up
                        else "adverse_first"
                    )
                    touch = minute
                    break
            assert label == row.outcome
            np.testing.assert_allclose(touch, row.first_touch_min, equal_nan=True)
            native_count += 1
    summary = pd.read_csv(DATA / "summary.csv")
    ledger = pd.read_parquet(DATA / "policy_executions.parquet")
    for row in summary.itertuples():
        full = {
            k: v
            for k, v in rows.items()
            if row.period == "pooled" or v.half == row.period
        }
        eligible = {
            k: v
            for k, v in full.items()
            if row.dataset == "combined"
            or (v.baseline if row.dataset == "baseline" else v.added)
        }
        picked = policy(eligible, row.policy)
        check_counts(picked, row)
        if row.period == "pooled" and row.dataset != "added_only":
            saved = ledger[
                (ledger.dataset == row.dataset) & (ledger.policy == row.policy)
            ]
            assert set(zip(saved.date, saved.known_min, strict=True)) == set(picked)
    changes = pd.read_csv(DATA / "policy_changes.csv")
    for row in changes.itertuples():
        full = {
            k: v
            for k, v in rows.items()
            if row.period == "pooled" or v.half == row.period
        }
        union = policy(full, row.policy)
        baseline = policy({k: v for k, v in full.items() if v.baseline}, row.policy)
        new, lost = union.keys() - baseline.keys(), baseline.keys() - union.keys()
        assert (
            len(new),
            sum(union[k].outcome == "target_first" for k in new),
            len(lost),
            sum(baseline[k].outcome == "target_first" for k in lost),
        ) == (row.newly_kept, row.newly_kept_wins, row.displaced, row.displaced_wins)
        assert row.net_n == len(new) - len(lost)
        assert row.net_wins == row.newly_kept_wins - row.displaced_wins
        assert row.new_active_dates == len(
            {d for d, _ in union} - {d for d, _ in baseline}
        )
    patterns = pd.read_csv(DATA / "added_route_patterns.csv")
    for row in patterns.itertuples():
        check_counts(
            {
                k: v
                for k, v in rows.items()
                if v.added
                and v.route_pattern == row.pattern
                and (row.period == "pooled" or v.half == row.period)
            },
            row,
        )
    novelty = pd.read_csv(DATA / "novel_dates.csv")
    baseline_dates = {d for (d, _), v in rows.items() if v.baseline}
    for row in novelty.itertuples():
        check_counts(
            {
                k: v
                for k, v in rows.items()
                if v.added
                and (row.period == "pooled" or v.half == row.period)
                and ((k[0] not in baseline_dates) == (row.date_group == "new_date"))
            },
            row,
        )
    loo = pd.read_csv(DATA / "leave_one_day_out.csv")
    for row in loo.itertuples():
        kept = [
            v
            for (d, _), v in rows.items()
            if d != row.removed_date
            and (row.period == "pooled" or v.half == row.period)
            and (row.dataset == "combined" or v.baseline)
        ]
        assert len(kept) == row.remaining_n
        assert sum(v.outcome == "target_first" for v in kept) == row.remaining_wins
    # Separate direct per-date recount of the pooled paired bootstrap.
    dates = calendar.date.tolist()
    n = np.array([sum(d == date for d, _ in rows) for date in dates])
    w = np.array(
        [
            sum(d == date and v.outcome == "target_first" for (d, _), v in rows.items())
            for date in dates
        ]
    )
    bn = np.array(
        [sum(d == date and v.baseline for (d, _), v in rows.items()) for date in dates]
    )
    bw = np.array(
        [
            sum(
                d == date and v.baseline and v.outcome == "target_first"
                for (d, _), v in rows.items()
            )
            for date in dates
        ]
    )
    draws = np.random.default_rng(20260920).multinomial(
        len(dates), np.repeat(1 / len(dates), len(dates)), size=5000
    )
    rates, brates = 100 * (draws @ w) / (draws @ n), 100 * (draws @ bw) / (draws @ bn)
    pooled = summary.query(
        "dataset == 'combined' and period == 'pooled' and policy == 'all'"
    ).iloc[0]
    np.testing.assert_allclose(
        np.quantile(rates, [0.025, 0.975]), [pooled.low, pooled.high], atol=1e-10
    )
    np.testing.assert_allclose(
        np.quantile(rates - brates, [0.025, 0.975]),
        [pooled.delta_low, pooled.delta_high],
        atol=1e-10,
    )
    record = dict(
        all_checks_passed=True,
        membership_timestamps=len(rows),
        native_entry_vt_outcome_replays=native_count,
        source_date_hashes=len(calendar),
        summary_rows=len(summary),
        policy_change_rows=len(changes),
        pattern_rows=len(patterns),
        novelty_rows=len(novelty),
        leave_one_day_out_rows=len(loo),
        pooled_paired_bootstrap_draws=5000,
        code_sha256=digest(OUT / "verify.py"),
    )
    write_json(DATA / "verification.json", record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
