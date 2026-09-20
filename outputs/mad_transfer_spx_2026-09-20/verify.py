"""Scalar membership, native first-touch and report-count replays."""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from prepare import DATA, HALVES, PREVIOUS, ROOT, SCORE, check_freeze, digest, save_json


def vote(m: float, a: float, b: float, rule: str) -> str:
    if rule.startswith("sign"):
        left = a < 0 if math.isfinite(m) and math.isfinite(a) else None
    else:
        left = m > 1 if math.isfinite(m) else None
    right = (b < -1e-12 if math.isfinite(b) else None) if rule in (
        "F4", "sign_falling4") else True
    if left is False or right is False:
        return "no"
    return "yes" if left is True and right is True else "unknown"


def select(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    kept, last = [], {}
    for row in frame.sort_values(["date", "known_min"]).itertuples():
        if mode == "all" or row.date not in last or (
                mode == "spaced60" and row.known_min - last[row.date] >= 60):
            kept.append(row.Index)
            last[row.date] = row.known_min
    return frame.loc[kept]


def restrict(frame: pd.DataFrame, cohort: str, period: str = "pooled") -> pd.DataFrame:
    if cohort in ["all11", "common_all11"]:
        frame = frame[frame.all11]
    if cohort.startswith("common"):
        frame = frame[frame.joint_measurable]
    if period == "completed":
        frame = frame[frame.half.isin(HALVES[:3])]
    elif period != "pooled":
        frame = frame[frame.half.eq(period)]
    return frame


def main() -> None:
    check_freeze()
    receipt = json.loads((DATA / "analysis_receipt.json").read_text())
    for path, expected in receipt["outputs"].items():
        if digest(Path(path)) != expected:
            raise ValueError(f"Changed analysis artifact: {path}")
    events = pd.read_parquet(DATA / "events_with_outcomes.parquet")
    sectors = pd.read_parquet(DATA / "sector_at_entry.parquet")
    members = pd.read_parquet(DATA / "memberships.parquet")
    spx = pd.read_parquet(DATA / "spx_at_entry.parquet").set_index("entry_id")
    scalar = {}
    for entry_id, group in sectors.groupby("entry_id", sort=False):
        for rule in ["S4", "F4", "sign4", "sign_falling4"]:
            c = Counter(vote(r.signed_score, r.acceleration, r.b2, rule) for r in group.itertuples())
            state = "yes" if c["yes"] >= 4 else "no" if c["yes"] + c["unknown"] < 4 else "unknown"
            scalar[entry_id, rule] = (state, c["yes"], c["unknown"])
    for entry_id, row in spx.iterrows():
        state = vote(row.signed_score, row.acceleration, row.b2, "F4")
        scalar[entry_id, "SPX_F"] = (state, int(state == "yes"), int(state == "unknown"))
        sector = scalar[entry_id, "F4"][0]
        union = "yes" if "yes" in [sector, state] else "no" if sector == state == "no" else "unknown"
        scalar[entry_id, "OR_F4_SPX"] = (union, -1, -1)
    for row in members.itertuples():
        if scalar[row.entry_id, row.rule] != (row.state, row.qualifying_votes, row.unknown_votes):
            raise ValueError("Scalar membership mismatch")
    wide = members.pivot(index="entry_id", columns="rule", values="state")
    for narrow, broad in [("F4", "S4"), ("S4", "sign4"), ("F4", "sign_falling4")]:
        if (wide[narrow].eq("yes") & ~wide[broad].eq("yes")).any():
            raise ValueError("Expected nesting violated")
    count = sectors.assign(valid=lambda x: x[["signed_score", "acceleration", "b2"]]
                            .notna().all(axis=1)).groupby("entry_id").valid.sum()
    np.testing.assert_array_equal(events.valid_sectors, events.entry_id.map(count))
    np.testing.assert_array_equal(events.all11, events.valid_sectors.eq(11))
    table = pd.read_csv(DATA / "summary.csv")
    for row in table.itertuples():
        frame = restrict(events[events.variant.eq(row.variant)], row.cohort, row.period)
        if row.rule != "baseline":
            states = frame.entry_id.map(wide[row.rule])
            frame = frame[states.ne("unknown") if row.state == "measurable" else states.eq(row.state)]
        frame = select(frame, row.mode)
        c = Counter(frame.outcome)
        actual = (len(frame), c["target_first"], c["adverse_first"], c["neither"],
                  c["ambiguous"], frame.date.nunique())
        expected = (row.n, row.targets, row.adverse_first, row.neither, row.ambiguous, row.days)
        if actual != expected:
            raise ValueError(f"Report mismatch: {row.variant}/{row.cohort}/{row.rule}/{row.period}/{row.mode}/{row.state}")
        np.testing.assert_allclose(row.rate, 100*c["target_first"]/len(frame) if len(frame) else np.nan,
                                   atol=1e-10, rtol=0, equal_nan=True)
    inherited = pd.read_csv(ROOT / "branch_b_iv_full_2024_2026_2026-09-19-v1/comparison.csv")
    inherited = inherited[inherited.variant.isin(["b09", "b07", "b05"])
                          & inherited.rule.eq("baseline") & inherited.period.isin(HALVES)]
    for row in inherited.itertuples():
        actual = table[table.variant.eq(row.variant) & table.cohort.eq("full")
                       & table.rule.eq("baseline") & table.period.eq(row.period)
                       & table["mode"].eq(row.mode)].iloc[0]
        if (actual.n, actual.targets, actual.days) != (row.n, row.targets, row.days):
            raise ValueError("Inherited half-year parent differs")
    old = pd.read_parquet(PREVIOUS / "memberships.parquet")
    for name, rule in [("S4", "signed_m1_b4"), ("F4", "falling_m1_b4")]:
        prior = old[old.rule.eq(rule)].set_index("entry_id")
        now = members[members.variant.eq("b09") & members.rule.eq(name)]
        keys = now.date + "|" + now.known_min.astype(str)
        np.testing.assert_array_equal(now.state, keys.map(prior.state))
    b09 = table[table.variant.eq("b09") & table.cohort.eq("full") & table.period.eq("pooled")
                & table["mode"].eq("all") & table.state.eq("yes")].set_index("rule")
    if (b09.loc["sign4", "n"], b09.loc["sign_falling4", "n"]) != (2544, 1933):
        raise ValueError("Reviewer sign-control counts not reproduced")
    days = pd.read_csv(DATA / "research_dates.csv", float_precision="round_trip")
    native = 0
    for day in days.itertuples():
        group = events[events.date.eq(day.date)]
        if not len(group):
            continue
        price = pd.read_parquet(day.source_path).set_index("min")
        for row in group.itertuples():
            start = int(row.known_min)
            entry = float(price.loc[start, "open"])
            if entry != row.entry_price or not (entry > day.vol_trigger and
                    price.loc[570:start-1, "low"].gt(day.vol_trigger).all()):
                raise ValueError("Entry/causal VT mismatch")
            outcome, touched = "neither", np.nan
            for minute in price.loc[start:start+59].itertuples():
                up, down = minute.high >= entry+5-1e-8, minute.low <= entry-10+1e-8
                if up or down:
                    outcome = "ambiguous" if up and down else "target_first" if up else "adverse_first"
                    touched = minute.Index
                    break
            if outcome != row.outcome or not (pd.isna(touched) and pd.isna(row.first_touch_min)
                                              or touched == row.first_touch_min):
                raise ValueError("Native first-touch outcome mismatch")
            native += 1
    diagnostics = pd.read_csv(DATA / "within_date_block.csv")
    for row in diagnostics.itertuples():
        frame = restrict(events[events.variant.eq(row.variant)], row.cohort, row.period).copy()
        frame["state"] = frame.entry_id.map(wide[row.rule])
        by_date = {}
        matched, yn, nn = 0, 0, 0
        for (date, _), block in frame.groupby(["date", "block"]):
            y, n = block[block.state.eq("yes")], block[block.state.eq("no")]
            if len(y) and len(n):
                matched += 1
                yn += len(y)
                nn += len(n)
                delta = 100*(y.outcome.eq("target_first").mean()-n.outcome.eq("target_first").mean())
                by_date.setdefault(date, []).append(delta)
        point = np.mean([np.mean(v) for v in by_date.values()]) if by_date else np.nan
        if (matched, yn, nn, len(by_date)) != (row.matched_strata, row.yes_n, row.no_n, row.dates):
            raise ValueError("Within-block support mismatch")
        np.testing.assert_allclose(row.equal_date_delta_pp, point, atol=1e-10, equal_nan=True)
    cross = pd.read_csv(DATA / "spx_cross.csv")
    for row in cross.itertuples():
        frame = restrict(events[events.variant.eq("b09")], row.cohort, row.period)
        frame = frame[frame.entry_id.map(wide.F4).eq(row.sector_state)
                      & frame.entry_id.map(wide.SPX_F).eq(row.spx_state)]
        frame = select(frame, row.mode)
        if (len(frame), int(frame.outcome.eq("target_first").sum())) != (row.n, row.targets):
            raise ValueError("SPX disagreement mismatch")
    result = dict(source_hashes_unchanged=True, scalar_memberships=len(members),
                  summary_rows=len(table), native_entry_vt_and_outcome_checks=native,
                  inherited_half_policy_baselines=len(inherited), within_block_rows=len(diagnostics),
                  spx_cross_rows=len(cross), prior_b09_memberships_reproduced=True,
                  reviewer_sign_controls_reproduced=True, all11_counts_verified=True,
                  nesting_verified=True, outcome_hash=digest(SCORE),
                  verification_code_sha256=digest(Path(__file__)),
                  review="Local scalar/native replays; no independent review of this new implementation")
    save_json(DATA / "verification.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
