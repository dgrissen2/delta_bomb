"""Independent scalar/raw-source replay of the bounded experiment."""

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from study import DATA, OLD, OUTCOMES, PRIOR, SPY, SYMBOLS, digest, write_json


def conjunction(values: list[bool | None]) -> str:
    if False in values:
        return "no"
    return "unknown" if None in values else "yes"


def predicate(value: float, which: str) -> bool | None:
    if not math.isfinite(value):
        return None
    return bool(value > 1 if which == "m" else value < -1e-12)


def scalar_persistence(
    group: pd.DataFrame, symbols: list[str], threshold: int
) -> tuple[str, int]:
    table = group.set_index(["symbol", "offset"])
    states = []
    for offset in range(5):
        votes = []
        for symbol in symbols:
            earlier = table.loc[(symbol, offset)]
            current = table.loc[(symbol, 4)]
            votes.append(
                conjunction(
                    [
                        predicate(earlier.signed_score, "m"),
                        predicate(earlier.b2, "b"),
                        predicate(current.b2, "b"),
                        True if math.isfinite(current.signed_score) else None,
                    ]
                )
            )
        c = Counter(votes)
        states.append(
            "yes"
            if c["yes"] >= threshold
            else "no"
            if c["yes"] + c["unknown"] < threshold
            else "unknown"
        )
    state = (
        "yes"
        if "yes" in states
        else "no"
        if all(s == "no" for s in states)
        else "unknown"
    )
    return state, states.index("yes") if state == "yes" else -1


def independent_policy(frame: pd.DataFrame, policy: str) -> pd.DataFrame:
    rows = []
    previous = {}
    seen = set()
    for row in frame.sort_values(["date", "known_min"]).itertuples():
        key = row.date, row.known_min
        if key in seen:
            continue
        seen.add(key)
        if (
            policy == "all"
            or row.date not in previous
            or (policy == "spaced60" and row.known_min - previous[row.date] >= 60)
        ):
            rows.append(row.Index)
            previous[row.date] = row.known_min
    return frame.loc[rows]


def check_counts(frame: pd.DataFrame, row: object) -> None:
    counts = Counter(frame.outcome)
    assert len(frame) == row.n and frame.date.nunique() == row.days
    for label in OUTCOMES:
        assert counts[label] == getattr(row, label)
    rate = 100 * counts["target_first"] / len(frame) if len(frame) else np.nan
    np.testing.assert_allclose(rate, row.rate, atol=1e-10, rtol=0, equal_nan=True)


def verify_volume() -> int:
    features = pd.read_parquet(DATA / "volume_features.parquet")
    raw = pd.read_parquet(SPY, columns=["date", "min", "volume"])
    raw["date"] = raw.date.astype(str)
    calendar = sorted(raw.date.unique())
    required = set(features.date)
    for history in features.history_dates:
        required.update(json.loads(history))
    raw = raw[raw.date.isin(required) & raw["min"].between(570, 959)]
    lookup = {(r.date, r.min): r.volume for r in raw.itertuples()}

    def window(date: str, minute: int) -> float:
        values = [lookup.get((date, t), np.nan) for t in range(minute - 5, minute)]
        return (
            sum(values) if all(math.isfinite(v) and v >= 0 for v in values) else np.nan
        )

    for r in features.itertuples():
        value = np.nan
        if r.date not in calendar:
            status = "current_unavailable"
        else:
            i = calendar.index(r.date)
            assert json.loads(r.history_dates) == (
                calendar[i - 60 : i] if i >= 60 else []
            )
            if i < 60:
                status = "insufficient_history"
            elif not math.isfinite(window(r.date, r.known_min)):
                status = "current_incomplete"
            else:
                history = [window(d, r.known_min) for d in calendar[i - 60 : i]]
                if not all(math.isfinite(v) for v in history):
                    status = "incomplete_history"
                elif np.median(history) <= 0:
                    status = "nonpositive_reference"
                else:
                    status = "ok"
                    value = window(r.date, r.known_min) / np.median(history)
        assert status == r.status
        np.testing.assert_allclose(value, r.rvol, atol=1e-12, equal_nan=True)
        assert r.state == (
            "yes" if value > 1 else "no" if math.isfinite(value) else "unknown"
        )
    return len(features)


def main() -> None:
    freeze = json.loads((DATA / "freeze.json").read_text())
    receipt = json.loads((DATA / "analysis_receipt.json").read_text())
    for hashes in [
        freeze["inputs"],
        freeze["outputs"],
        freeze["code_protocol"],
        receipt["outputs"],
        receipt["outcome_source"],
    ]:
        for p, h in hashes.items():
            assert digest(Path(p)) == h, p
    assert digest(Path(__file__).with_name("analyze.py")) == receipt["code_hash"]
    m = pd.read_parquet(DATA / "memberships.parquet").set_index("entry_id")
    support = pd.read_parquet(DATA / "persistence_sources.parquet")
    scalar_count = 0
    for entry_id, group in support.groupby("entry_id", sort=False):
        assert len(group) == 60 and not group.duplicated(["symbol", "offset"]).any()
        assert (group.end_min == group.known_min - 5 + group.offset).all()
        row = m.loc[entry_id]
        sector, sw = scalar_persistence(group, SYMBOLS, 4)
        index, iw = scalar_persistence(group, ["SPXW"], 1)
        assert sector == row.sector_persist_state and index == row.spx_persist_state
        assert row.sector_witness_min == (row.known_min - 5 + sw if sw >= 0 else -1)
        assert row.spx_witness_min == (row.known_min - 5 + iw if iw >= 0 else -1)
        state = (
            "yes"
            if "yes" in [sector, index]
            else "no"
            if sector == index == "no"
            else "unknown"
        )
        assert state == row.persistence_state
        scalar_count += 1
    print("Scalar persistence:", scalar_count, flush=True)
    sf = pd.read_parquet(
        OLD / "sector_features.parquet",
        columns=[
            "date",
            "known_min",
            "symbol",
            "original_available",
            "original_b2",
            "original_acceleration",
        ],
    )
    groups = {(d, t): f for (d, t), f in sf.groupby(["date", "known_min"])}
    b07_count = 0
    for r in m[m.variant.eq("b07")].itertuples():
        group = groups[(r.date, r.known_min)]
        assert sorted(group.symbol) == SYMBOLS
        votes = [
            "unknown"
            if not x.original_available
            else "yes"
            if x.original_b2 < -1e-12 and x.original_acceleration < -1e-12
            else "no"
            for x in group.itertuples()
        ]
        c = Counter(votes)
        expected = (
            "yes"
            if c["yes"] >= 6
            else "no"
            if c["yes"] + c["unknown"] < 6
            else "unknown"
        )
        assert expected == r.original_accelerating_6
        b07_count += 1
    volume_count = verify_volume()
    print(
        "B07 original votes:",
        b07_count,
        "Raw volume features:",
        volume_count,
        flush=True,
    )
    e = pd.read_parquet(DATA / "executions.parquet")
    parent = pd.read_parquet(PRIOR / "events_with_outcomes.parquet")
    native = 0
    dates = pd.read_csv(DATA / "research_dates.csv", float_precision="round_trip")
    for d in dates.itertuples():
        price = pd.read_parquet(d.source_path).set_index("min")
        for r in parent[parent.date.eq(d.date)].itertuples():
            start, entry = r.known_min, price.loc[r.known_min, "open"]
            assert entry == r.entry_price and entry > d.vol_trigger
            assert price.loc[570 : start - 1, "low"].gt(d.vol_trigger).all()
            label, touch = "neither", np.nan
            for bar in price.loc[start : start + 59].itertuples():
                up, down = bar.high >= entry + 5 - 1e-8, bar.low <= entry - 10 + 1e-8
                if up or down:
                    label = (
                        "ambiguous"
                        if up and down
                        else "target_first"
                        if up
                        else "adverse_first"
                    )
                    touch = bar.Index
                    break
            assert label == r.outcome
            assert (
                touch == r.first_touch_min
                or math.isnan(touch)
                and math.isnan(r.first_touch_min)
            )
            native += 1
    summary = pd.read_csv(DATA / "summary.csv")
    for r in summary.itertuples():
        part = e[e.dataset.eq(r.dataset)]
        if r.period != "pooled":
            part = part[part.half.eq(r.period)]
        check_counts(independent_policy(part, r.policy), r)
    vs = pd.read_csv(DATA / "volume_summary.csv")
    ve = pd.read_parquet(DATA / "volume_events.parquet")
    for r in vs.itertuples():
        part = ve[ve.baseline] if r.cohort == "base_or" else ve
        if r.period != "pooled":
            part = part[part.half.eq(r.period)]
        part = (
            part[part.volume_state.ne("unknown")]
            if r.state == "observed"
            else part[part.volume_state.eq(r.state)]
        )
        check_counts(independent_policy(part, r.policy), r)
    loo = pd.read_csv(DATA / "leave_one_day_out.csv")
    for r in loo.itertuples():
        part = e[e.dataset.eq(r.dataset) & e.date.ne(r.date)]
        if r.period != "pooled":
            part = part[part.half.eq(r.period)]
        assert len(part) == r.remaining_n
        assert int(part.outcome.eq("target_first").sum()) == r.remaining_wins
    changes = pd.read_csv(DATA / "policy_changes.csv")
    for r in changes.itertuples():
        a, b = e[e.dataset.eq(r.dataset)], e[e.dataset.eq("baseline")]
        if r.period != "pooled":
            a, b = a[a.half.eq(r.period)], b[b.half.eq(r.period)]
        a, b = independent_policy(a, r.policy), independent_policy(b, r.policy)
        aa = {(x.date, x.known_min): x.outcome for x in a.itertuples()}
        bb = {(x.date, x.known_min): x.outcome for x in b.itertuples()}
        added, removed = aa.keys() - bb.keys(), bb.keys() - aa.keys()
        assert (
            len(added),
            sum(aa[k] == "target_first" for k in added),
            len(removed),
            sum(bb[k] == "target_first" for k in removed),
        ) == (r.newly_kept, r.newly_kept_wins, r.displaced, r.displaced_wins)
        assert len(set(a.date) - set(b.date)) == r.new_dates
    controls = pd.read_csv(DATA / "volume_within_block.csv")
    for r in controls.itertuples():
        part = ve[ve.baseline] if r.cohort == "base_or" else ve
        daily_deltas = {}
        matched, yes_n, no_n = 0, 0, 0
        for (date, _), g in part.groupby(["date", "block"]):
            y, n = g[g.volume_state.eq("yes")], g[g.volume_state.eq("no")]
            if len(y) and len(n):
                matched += 1
                yes_n += len(y)
                no_n += len(n)
                daily_deltas.setdefault(date, []).append(
                    100
                    * (
                        y.outcome.eq("target_first").mean()
                        - n.outcome.eq("target_first").mean()
                    )
                )
        assert (len(daily_deltas), matched, yes_n, no_n) == (
            r.dates,
            r.kept_strata,
            r.yes_n,
            r.no_n,
        )
        np.testing.assert_allclose(
            np.mean([np.mean(v) for v in daily_deltas.values()]), r.delta
        )
    results = dict(
        scalar_persistence_events=scalar_count,
        original_b07_vote_replays=b07_count,
        raw_volume_replays=volume_count,
        native_vt_outcome_replays=native,
        summary_rows=len(summary),
        volume_summary_rows=len(vs),
        day_deletion_rows=len(loo),
        chronological_policy_changes=len(changes),
        volume_block_controls=len(controls),
        all_hashes_verified=True,
        verification_code_hash=digest(Path(__file__)),
        review="Local independent-formula/raw-source verification, not independent Claude review",
    )
    write_json(DATA / "verification.json", results)
    print(json.dumps(results), flush=True)


if __name__ == "__main__":
    main()
