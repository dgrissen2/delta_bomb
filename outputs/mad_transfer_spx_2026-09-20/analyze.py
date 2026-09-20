"""Attach frozen outcomes and report the bounded reviewed comparisons."""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from logic import RULES, describe, thin, within_blocks
from prepare import DATA, MODES, PERIODS, SCORE, check_freeze, digest, period_rows, save_json


class DateBootstrap:
    """Shared whole-date draws, preserving all within-date entry dependence."""

    def __init__(self, dates: list[str]) -> None:
        self.dates = dates
        self.weights = np.random.default_rng(20260920).multinomial(
            len(dates), np.full(len(dates), 1 / len(dates)), size=5000)

    def rates(self, frame: pd.DataFrame) -> np.ndarray:
        daily = frame.assign(hit=frame.outcome.eq("target_first").astype(int)).groupby("date").agg(
            n=("hit", "size"), wins=("hit", "sum")).reindex(self.dates, fill_value=0)
        n, wins = self.weights @ daily.n.to_numpy(), self.weights @ daily.wins.to_numpy()
        return np.divide(100. * wins, n, out=np.full(len(n), np.nan), where=n > 0)

    def means(self, daily: pd.DataFrame) -> np.ndarray:
        x = daily.set_index("date").delta.reindex(self.dates)
        n = self.weights @ x.notna().to_numpy(dtype=int)
        total = self.weights @ x.fillna(0).to_numpy()
        return np.divide(total, n, out=np.full(len(n), np.nan), where=n > 0)


def bounds(values: np.ndarray, support: pd.DataFrame) -> tuple[float, float]:
    finite = values[np.isfinite(values)]
    if support.date.nunique() < 2 or len(finite) == 0:
        return np.nan, np.nan
    if "outcome" in support and support.outcome.eq("target_first").nunique() < 2:
        return np.nan, np.nan
    return tuple(float(x) for x in np.quantile(finite, [.025, .975]))


def comparison(boot: DateBootstrap, selected: pd.DataFrame, reference: pd.DataFrame) -> dict:
    """Return observed contrast and descriptive intervals; no significance flag."""
    s, r = describe(selected), describe(reference)
    values, ref = boot.rates(selected), boot.rates(reference)
    low, high = bounds(values, selected)
    dl, dh = bounds(values - ref, selected)
    if reference.date.nunique() < 2:
        dl, dh = np.nan, np.nan
    return dict(n=s["n"], targets=s["targets"], days=s["days"], rate=s["rate"],
                reference_n=r["n"], reference_days=r["days"], reference_rate=r["rate"],
                delta_pp=s["rate"] - r["rate"], low=low, high=high,
                delta_low=dl, delta_high=dh,
                finite_draws=int(np.isfinite(values - ref).sum()), draws=5000,
                interpretation="unestimable" if not s["n"] or not r["n"] else
                "exploratory; sparse/wide intervals can be underpowered")


def cases(events: pd.DataFrame, wide: pd.DataFrame):
    """The same fixed rules on declared full/coverage-restricted populations."""
    for variant in ["b09", "b07", "b05"]:
        pool = events[events.variant.eq(variant)]
        rules = list(RULES) + (["SPX_F", "OR_F4_SPX"] if variant == "b09" else [])
        for cohort in ["full", "all11"]:
            parent = pool if cohort == "full" else pool[pool.all11]
            for rule in rules:
                frame = parent.copy()
                frame["state"] = frame.entry_id.map(wide[rule])
                if frame.state.isna().any():
                    raise ValueError("Missing membership")
                yield variant, cohort, rule, frame
        if variant == "b09":
            for cohort in ["common", "common_all11"]:
                parent = pool[pool.joint_measurable & (pool.all11 if cohort.endswith("all11") else True)]
                for rule in ["F4", "SPX_F", "OR_F4_SPX"]:
                    frame = parent.copy()
                    frame["state"] = frame.entry_id.map(wide[rule])
                    yield variant, cohort, rule, frame


def summaries(events: pd.DataFrame, wide: pd.DataFrame) -> pd.DataFrame:
    records, seen_baseline = [], set()
    for variant, cohort, rule, frame in cases(events, wide):
        for period in PERIODS:
            pool = period_rows(frame, period)
            for mode in MODES:
                base = thin(pool, mode)
                stats = describe(base)
                key = variant, cohort, period, mode
                if key not in seen_baseline:
                    records.append(dict(variant=variant, cohort=cohort, period=period,
                                        mode=mode, rule="baseline", state="all", **stats))
                    seen_baseline.add(key)
                base_winners = set(base.loc[base.outcome.eq("target_first"), "entry_id"])
                for state in ["yes", "no", "unknown", "measurable"]:
                    selected = thin(pool[pool.state.ne("unknown") if state == "measurable"
                                         else pool.state.eq(state)], mode)
                    result = describe(selected)
                    selected_date_parent = thin(pool[pool.date.isin(selected.date)], mode)
                    ds = describe(selected_date_parent)
                    wins = set(selected.loc[selected.outcome.eq("target_first"), "entry_id"])
                    records.append(dict(variant=variant, cohort=cohort, period=period, mode=mode,
                        rule=rule, state=state, **result, parent_n=stats["n"],
                        parent_targets=stats["targets"], parent_days=stats["days"],
                        parent_rate=stats["rate"], uplift_pp=result["rate"]-stats["rate"],
                        parent_winner_overlap=len(wins & base_winners),
                        parent_winners_excluded=len(base_winners-wins),
                        same_dates_parent_n=ds["n"], same_dates_parent_rate=ds["rate"],
                        same_dates_delta_pp=result["rate"]-ds["rate"]))
    return pd.DataFrame(records)


def uncertainty(events: pd.DataFrame, wide: pd.DataFrame, boot: DateBootstrap) -> pd.DataFrame:
    records = []
    for variant, cohort, rule, frame in cases(events, wide):
        for mode in MODES:
            yes = thin(frame[frame.state.eq("yes")], mode)
            refs = {"parent": thin(frame, mode),
                    "definite_no": thin(frame[frame.state.eq("no")], mode),
                    "measurable": thin(frame[frame.state.ne("unknown")], mode),
                    "same_selected_dates": thin(frame[frame.date.isin(yes.date)], mode)}
            if rule in ["S4", "F4"]:
                sign = "sign4" if rule == "S4" else "sign_falling4"
                refs["corresponding_sign_control"] = thin(
                    frame[frame.entry_id.map(wide[sign]).eq("yes")], mode)
            for name, ref in refs.items():
                records.append(dict(variant=variant, cohort=cohort, rule=rule, mode=mode,
                                    reference=name, **comparison(boot, yes, ref)))
    return pd.DataFrame(records)


def date_hour_diagnostics(events: pd.DataFrame, wide: pd.DataFrame,
                          boot: DateBootstrap) -> tuple[pd.DataFrame, pd.DataFrame]:
    records, details = [], []
    for variant, cohort, rule, frame in cases(events, wide):
        for period in PERIODS:
            pool = period_rows(frame, period).assign(hit=lambda x: x.outcome.eq("target_first").astype(int))
            detail, daily = within_blocks(pool)
            detail["variant"], detail["cohort"], detail["rule"] = variant, cohort, rule
            detail["period"] = period
            details.append(detail)
            values = boot.means(daily)
            low, high = bounds(values, daily)
            kept = detail[detail.both]
            records.append(dict(variant=variant, cohort=cohort, rule=rule, period=period,
                strata=len(detail), matched_strata=len(kept), discarded_strata=len(detail)-len(kept),
                yes_n=int(kept.yes_n.sum()), no_n=int(kept.no_n.sum()),
                unmatched_yes_n=int(detail[~detail.both].yes_n.sum()),
                unmatched_no_n=int(detail[~detail.both].no_n.sum()),
                unknown_n=int(detail.unknown_n.sum()), dates=len(daily),
                equal_date_delta_pp=float(daily.delta.mean()) if len(daily) else np.nan,
                low=low, high=high, finite_draws=int(np.isfinite(values).sum()),
                interpretation="unestimable: no two-sided strata" if not len(daily)
                else "descriptive within-date/block; not causal; inspect support/uncertainty"))
    return pd.DataFrame(records), pd.concat(details, ignore_index=True)


def overlap_diagnostics(events: pd.DataFrame, wide: pd.DataFrame) -> pd.DataFrame:
    records = []
    for rule in ["S4", "F4"]:
        b09 = events[events.variant.eq("b09") & events.entry_id.map(wide[rule]).eq("yes")]
        blocks = set(zip(b09.date, b09.block))
        minutes = set(zip(b09.date, b09.known_min))
        for variant in ["b07", "b05"]:
            for cohort in ["full", "all11"]:
                parent = events[events.variant.eq(variant)]
                if cohort == "all11":
                    parent = parent[parent.all11]
                for split in ["with_b09_block", "without_b09_block", "exact_b09_minute"]:
                    flag = np.array([(r.date, r.known_min) in minutes if split == "exact_b09_minute"
                                     else (r.date, r.block) in blocks for r in parent.itertuples()], dtype=bool)
                    if split == "without_b09_block":
                        flag = ~flag
                    part = parent[flag]
                    for period in PERIODS:
                        scope = period_rows(part, period)
                        for mode in MODES:
                            for state in ["all", "yes", "no", "unknown"]:
                                subset = scope if state == "all" else scope[
                                    scope.entry_id.map(wide[rule]).eq(state)]
                                records.append(dict(variant=variant, cohort=cohort, rule=rule,
                                    split=split, period=period, mode=mode, state=state,
                                    **describe(thin(subset, mode))))
    return pd.DataFrame(records)


def spx_diagnostics(events: pd.DataFrame, wide: pd.DataFrame,
                    boot: DateBootstrap) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    b09 = events[events.variant.eq("b09")].copy()
    b09["sector_state"] = b09.entry_id.map(wide.F4)
    b09["spx_state"] = b09.entry_id.map(wide.SPX_F)
    records, incremental, intervals = [], [], []
    for cohort in ["full", "all11"]:
        pool = b09 if cohort == "full" else b09[b09.all11]
        for period in PERIODS:
            parent = period_rows(pool, period)
            for mode in MODES:
                for sector in ["yes", "no", "unknown"]:
                    for spx in ["yes", "no", "unknown"]:
                        subset = parent[parent.sector_state.eq(sector) & parent.spx_state.eq(spx)]
                        records.append(dict(cohort=cohort, period=period, mode=mode,
                            sector_state=sector, spx_state=spx, **describe(thin(subset, mode))))
                groups = {
                    "added_sector_no": parent[parent.sector_state.eq("no") & parent.spx_state.eq("yes")],
                    "added_sector_unknown": parent[parent.sector_state.eq("unknown") & parent.spx_state.eq("yes")],
                    "sector_no_spx_no": parent[parent.sector_state.eq("no") & parent.spx_state.eq("no")],
                    "joint_sector_no": parent[parent.sector_state.eq("no") & parent.spx_state.ne("unknown")],
                }
                for group, subset in groups.items():
                    incremental.append(dict(cohort=cohort, period=period, mode=mode, group=group,
                                            **describe(thin(subset, mode))))
        for mode in MODES:
            yes = thin(pool[pool.sector_state.eq("no") & pool.spx_state.eq("yes")], mode)
            for reference, ref in {
                "sector_no_spx_no": pool[pool.sector_state.eq("no") & pool.spx_state.eq("no")],
                "joint_sector_no": pool[pool.sector_state.eq("no") & pool.spx_state.ne("unknown")],
            }.items():
                intervals.append(dict(cohort=cohort, mode=mode, reference=reference,
                                      **comparison(boot, yes, thin(ref, mode))))
    return pd.DataFrame(records), pd.DataFrame(incremental), pd.DataFrame(intervals)


def main() -> None:
    freeze = check_freeze()
    if (DATA / "analysis_receipt.json").exists():
        raise FileExistsError("Completed study already exists")
    keys = pd.read_parquet(DATA / "event_keys.parquet")
    cols = ["date", "variant", "known_min", "outcome", "entry_price", "first_touch_min"]
    raw = pd.read_parquet(SCORE, columns=cols)
    raw = raw[raw.variant.isin(["b09", "b07", "b05"])
              & raw.date.between("2025-01-01", "2026-09-18")]
    for column in ["outcome", "entry_price", "first_touch_min"]:
        if raw.groupby(["variant", "date", "known_min"])[column].nunique(dropna=False).gt(1).any():
            raise ValueError("Duplicate parent outcomes disagree")
    events = keys.merge(raw.drop_duplicates(["variant", "date", "known_min"]),
                        on=["variant", "date", "known_min"], how="left", validate="one_to_one")
    if events.outcome.isna().any():
        raise ValueError("Missing unchanged outcome")
    membership = pd.read_parquet(DATA / "memberships.parquet")
    wide = membership.pivot(index="entry_id", columns="rule", values="state")
    events.to_parquet(DATA / "events_with_outcomes.parquet", index=False)
    boot = DateBootstrap(pd.read_csv(DATA / "research_dates.csv").date.tolist())
    table = summaries(events, wide)
    table.to_csv(DATA / "summary.csv", index=False)
    print("Primary, control and SPX summaries complete", flush=True)
    uncertainty(events, wide, boot).to_csv(DATA / "uncertainty.csv", index=False)
    print("Shared whole-date uncertainty complete", flush=True)
    blocks, strata = date_hour_diagnostics(events, wide, boot)
    blocks.to_csv(DATA / "within_date_block.csv", index=False)
    strata.to_csv(DATA / "within_date_block_strata.csv", index=False)
    overlap_diagnostics(events, wide).to_csv(DATA / "b09_overlap.csv", index=False)
    cross, added, ci = spx_diagnostics(events, wide, boot)
    cross.to_csv(DATA / "spx_cross.csv", index=False)
    added.to_csv(DATA / "spx_incremental.csv", index=False)
    ci.to_csv(DATA / "spx_incremental_uncertainty.csv", index=False)
    outputs = {str(p): digest(p) for p in DATA.iterdir()
               if p.is_file() and str(p) not in freeze["output_hashes"] and p.name != "freeze.json"}
    save_json(DATA / "analysis_receipt.json", dict(at=datetime.now(timezone.utc).isoformat(),
        freeze_sha256=digest(DATA / "freeze.json"), outputs=outputs,
        outcome_sha256=digest(SCORE), bootstraps=5000, seed=20260920,
        multiple_comparison_adjustment="none; exploratory on reused research dates"))
    print(table[table.cohort.eq("full") & table.period.eq("pooled") & table["mode"].eq("all")
                & table.state.isin(["all", "yes"])][
                    ["variant", "rule", "n", "targets", "days", "rate"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
