"""Score only the frozen comparisons; no parameter selection."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from study import (
    DATA,
    HALVES,
    PRIOR,
    describe,
    difference,
    digest,
    keys,
    thin,
    unique,
    write_json,
)


def interval(values: np.ndarray, frame: pd.DataFrame) -> tuple[float, float, int]:
    good = values[np.isfinite(values)]
    if (
        frame.date.nunique() < 2
        or frame.outcome.eq("target_first").nunique() < 2
        or not len(good)
    ):
        return np.nan, np.nan, len(good)
    low, high = np.quantile(good, [0.025, 0.975])
    return float(low), float(high), len(good)


def daily(frame: pd.DataFrame, dates: list[str]) -> pd.DataFrame:
    result = (
        frame.assign(hit=frame.outcome.eq("target_first"))
        .groupby("date")
        .agg(n=("outcome", "size"), wins=("hit", "sum"))
        .reindex(dates, fill_value=0)
    )
    return result


def bootstrap(frame: pd.DataFrame, dates: list[str], draws: np.ndarray) -> np.ndarray:
    d = daily(frame, dates)
    n, w = draws @ d.n.to_numpy(), draws @ d.wins.to_numpy()
    return np.divide(100.0 * w, n, out=np.full(len(n), np.nan), where=n > 0)


def summary_row(
    frame: pd.DataFrame, reference: pd.DataFrame, dates: list[str], draws: np.ndarray
) -> dict:
    rate = bootstrap(frame, dates, draws)
    ref = bootstrap(reference, dates, draws)
    low, high, valid = interval(rate, frame)
    delta = rate - ref
    finite = delta[np.isfinite(delta)]
    dlo, dhi = (
        np.quantile(finite, [0.025, 0.975])
        if len(finite) and frame.date.nunique() >= 2 and reference.date.nunique() >= 2
        else (np.nan, np.nan)
    )
    d = daily(frame, dates)
    return describe(frame) | dict(
        low=low,
        high=high,
        finite_draws=valid,
        delta_vs_reference_pp=describe(frame)["rate"] - describe(reference)["rate"],
        delta_low=dlo,
        delta_high=dhi,
        delta_finite_draws=len(finite),
        median_per_research_day=float(d.n.median()),
        median_per_active_day=float(d.loc[d.n.gt(0), "n"].median()),
        research_days=len(dates),
    )


def volume_controls(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Equal-block then equal-day yes-minus-no; price balance is descriptive."""
    details, summaries, balances = [], [], []
    for cohort, part in [("all_b09", frame), ("base_or", frame[frame.baseline])]:
        for state, group in part.groupby("volume_state"):
            balances.append(
                dict(
                    cohort=cohort,
                    state=state,
                    n=len(group),
                    return30_mean=group.return30_bps.mean(),
                    return30_median=group.return30_bps.median(),
                    rv30_mean=group.rv30_points.mean(),
                    rv30_median=group.rv30_points.median(),
                    rvol_median=group.rvol.median(),
                )
            )
        for (date, block), group in part.groupby(["date", "block"]):
            yes, no = (
                group[group.volume_state.eq("yes")],
                group[group.volume_state.eq("no")],
            )
            both = bool(len(yes) and len(no))
            details.append(
                dict(
                    cohort=cohort,
                    date=date,
                    block=block,
                    yes_n=len(yes),
                    no_n=len(no),
                    unknown_n=int(group.volume_state.eq("unknown").sum()),
                    both=both,
                    delta=describe(yes)["rate"] - describe(no)["rate"]
                    if both
                    else np.nan,
                    return_difference=yes.return30_bps.mean() - no.return30_bps.mean()
                    if both
                    else np.nan,
                    rv_difference=yes.rv30_points.mean() - no.rv30_points.mean()
                    if both
                    else np.nan,
                )
            )
    strata = pd.DataFrame(details)
    for cohort, group in strata.groupby("cohort"):
        kept = group[group.both]
        days = kept.groupby("date").delta.mean()
        rng = np.random.default_rng(20260920)
        if len(days) >= 2:
            draws = rng.multinomial(
                len(days), np.repeat(1 / len(days), len(days)), size=5000
            )
            low, high = np.quantile(draws @ days.to_numpy() / len(days), [0.025, 0.975])
        else:
            low, high = np.nan, np.nan
        summaries.append(
            dict(
                cohort=cohort,
                delta=days.mean(),
                low=low,
                high=high,
                dates=len(days),
                kept_strata=len(kept),
                all_strata=len(group),
                yes_n=int(kept.yes_n.sum()),
                no_n=int(kept.no_n.sum()),
                equal_date_return_difference=kept.groupby("date")
                .return_difference.mean()
                .mean(),
                equal_date_rv_difference=kept.groupby("date")
                .rv_difference.mean()
                .mean(),
            )
        )
    return strata, pd.DataFrame(summaries), pd.DataFrame(balances)


def main() -> None:
    freeze = json.loads((DATA / "freeze.json").read_text())
    for group in ["inputs", "outputs", "code_protocol"]:
        for path, expected in freeze[group].items():
            if digest(Path(path)) != expected:
                raise ValueError(f"Frozen file changed: {path}")
    source = PRIOR / "events_with_outcomes.parquet"
    old_receipt = json.loads((PRIOR / "analysis_receipt.json").read_text())
    assert digest(source) == old_receipt["outputs"][str(source)]
    outcomes = pd.read_parquet(
        source, columns=["entry_id", "outcome", "entry_price", "first_touch_min"]
    )
    m = pd.read_parquet(DATA / "memberships.parquet")
    events = m.merge(outcomes, on="entry_id", validate="one_to_one")
    assert len(events) == len(m) == 5093
    base = unique(events[events.baseline])
    assert (len(base), int(base.outcome.eq("target_first").sum())) == (318, 198)
    b05 = events[events.b05_candidate]
    assert (len(b05), int(b05.outcome.eq("target_first").sum())) == (112, 70)
    candidates = {
        "b05": b05,
        "persistence": events[events.persistence_candidate],
        "b07": events[events.b07_candidate],
    }
    datasets = {"baseline": base}
    overlaps = []
    for label, candidate in candidates.items():
        merged = unique(pd.concat([base, candidate], ignore_index=True))
        added = difference(merged, base)
        datasets[label + "_union"] = merged
        datasets[label + "_added"] = added
        assert keys(base).issubset(keys(merged))
        assert keys(base).isdisjoint(keys(added))
        for r in added.itertuples():
            mins = base.loc[base.date.eq(r.date), "known_min"].to_numpy()
            gaps = r.known_min - mins
            overlaps.append(
                dict(
                    candidate=label,
                    date=r.date,
                    known_min=r.known_min,
                    outcome=r.outcome,
                    new_date=len(mins) == 0,
                    base_within_previous_60=bool(((gaps > 0) & (gaps < 60)).any()),
                    base_within_either_60=bool((np.abs(gaps) < 60).any()),
                    nearest_base_minutes=int(np.abs(gaps).min())
                    if len(gaps)
                    else np.nan,
                )
            )
    dates_frame = pd.read_csv(DATA / "research_dates.csv")
    dates_frame["half"] = dates_frame.date.map(
        lambda d: f"{d[:4]}_H{(int(d[5:7]) - 1) // 6 + 1}"
    )
    summary, moves, leaveout, influence, vol_rows, cross_rows = [], [], [], [], [], []
    volume = pd.read_parquet(DATA / "volume_features.parquet").rename(
        columns={"state": "volume_state"}
    )
    v = events[events.variant.eq("b09")].merge(
        volume.drop(columns=["date", "known_min"]), on="entry_id", validate="one_to_one"
    )
    for period in ["pooled", *HALVES]:
        dates = dates_frame.loc[
            dates_frame.half.eq(period)
            if period != "pooled"
            else np.ones(len(dates_frame), dtype=bool),
            "date",
        ].tolist()
        rng = np.random.default_rng(20260920)
        draws = rng.multinomial(
            len(dates), np.repeat(1 / len(dates), len(dates)), size=5000
        )
        period_base = base[base.date.isin(dates)]
        for policy in ["all", "first", "spaced60"]:
            reference = thin(period_base, policy)
            for label, full in datasets.items():
                frame = thin(full[full.date.isin(dates)], policy)
                summary.append(
                    dict(
                        dataset=label,
                        period=period,
                        policy=policy,
                        **summary_row(frame, reference, dates, draws),
                    )
                )
                if label.endswith("_union"):
                    added, removed = (
                        difference(frame, reference),
                        difference(reference, frame),
                    )
                    moves.append(
                        dict(
                            dataset=label,
                            period=period,
                            policy=policy,
                            newly_kept=len(added),
                            newly_kept_wins=int(added.outcome.eq("target_first").sum()),
                            displaced=len(removed),
                            displaced_wins=int(
                                removed.outcome.eq("target_first").sum()
                            ),
                            net_n=len(frame) - len(reference),
                            net_wins=int(
                                frame.outcome.eq("target_first").sum()
                                - reference.outcome.eq("target_first").sum()
                            ),
                            new_dates=len(set(frame.date) - set(reference.date)),
                        )
                    )
            part = v[v.date.isin(dates)]
            for cohort, full in [("all_b09", part), ("base_or", part[part.baseline])]:
                observed = full[full.volume_state.ne("unknown")]
                ref = thin(full[full.volume_state.eq("no")], policy)
                for state in ["observed", "yes", "no", "unknown"]:
                    raw = (
                        observed
                        if state == "observed"
                        else full[full.volume_state.eq(state)]
                    )
                    f = thin(raw, policy)
                    vol_rows.append(
                        dict(
                            cohort=cohort,
                            period=period,
                            policy=policy,
                            state=state,
                            **summary_row(f, ref, dates, draws),
                        )
                    )
        for label in ["baseline", "b05_union", "persistence_union", "b07_union"]:
            f = datasets[label]
            f = f[f.date.isin(dates)]
            d = daily(f, dates)
            total_n, total_w = len(f), int(f.outcome.eq("target_first").sum())
            remaining = np.where(
                total_n - d.n > 0, 100 * (total_w - d.wins) / (total_n - d.n), np.nan
            )
            for date, row, rate in zip(d.index, d.itertuples(), remaining, strict=True):
                leaveout.append(
                    dict(
                        dataset=label,
                        period=period,
                        date=date,
                        removed_n=row.n,
                        removed_wins=row.wins,
                        remaining_n=total_n - row.n,
                        remaining_wins=total_w - row.wins,
                        remaining_rate=rate,
                    )
                )
            influence.append(
                dict(
                    dataset=label,
                    period=period,
                    min_rate=float(np.nanmin(remaining)),
                    max_rate=float(np.nanmax(remaining)),
                    top_day_wins=int(d.wins.max()),
                    top5_wins=int(d.wins.nlargest(5).sum()),
                    total_wins=total_w,
                )
            )
        for (old_state, volume_state), group in v[v.date.isin(dates)].groupby(
            ["base_state", "volume_state"]
        ):
            cross_rows.append(
                dict(
                    period=period,
                    base_state=old_state,
                    volume_state=volume_state,
                    **describe(group),
                )
            )
    executions = pd.concat(
        [f.assign(dataset=name) for name, f in datasets.items()], ignore_index=True
    )
    executions.to_parquet(DATA / "executions.parquet", index=False)
    v.to_parquet(DATA / "volume_events.parquet", index=False)
    strata, control_summary, balance = volume_controls(v)
    tables = {
        "summary.csv": pd.DataFrame(summary),
        "policy_changes.csv": pd.DataFrame(moves),
        "addition_overlap.csv": pd.DataFrame(overlaps),
        "leave_one_day_out.csv": pd.DataFrame(leaveout),
        "day_influence_summary.csv": pd.DataFrame(influence),
        "volume_summary.csv": pd.DataFrame(vol_rows),
        "volume_cross.csv": pd.DataFrame(cross_rows),
        "volume_strata.csv": strata,
        "volume_within_block.csv": control_summary,
        "volume_context_balance.csv": balance,
    }
    for name, frame in tables.items():
        frame.to_csv(DATA / name, index=False)
    outputs = {
        str(DATA / name): digest(DATA / name)
        for name in [*tables, "executions.parquet", "volume_events.parquet"]
    }
    write_json(
        DATA / "analysis_receipt.json",
        dict(
            outcome_source={str(source): digest(source)},
            code_hash=digest(Path(__file__)),
            freeze_hash=digest(DATA / "freeze.json"),
            outputs=outputs,
            bootstrap_draws=5000,
            bootstrap_seed=20260920,
        ),
    )
    s = tables["summary.csv"]
    print(
        s[s.period.eq("pooled") & s.policy.eq("all")][
            [
                "dataset",
                "target_first",
                "n",
                "days",
                "rate",
                "low",
                "high",
                "delta_low",
                "delta_high",
            ]
        ].to_string(index=False)
    )
    print("VOLUME")
    z = tables["volume_summary.csv"]
    print(
        z[z.period.eq("pooled") & z.policy.eq("all")][
            [
                "cohort",
                "state",
                "target_first",
                "n",
                "days",
                "rate",
                "delta_low",
                "delta_high",
            ]
        ].to_string(index=False)
    )
    print("Within-block volume:", control_summary.to_dict("records"))


if __name__ == "__main__":
    main()
