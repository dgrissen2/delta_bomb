"""Enrich frozen episodes from local pre-signal data; no provider calls or trade filtering.

Compass-style ranks use 30-day inputs and the prior 252 supplied exchange sessions,
minimum 100 valid values, strict-below counting, and separate 0–1/0–100 columns.
They are labeled SpotGamma-compatible reconstructions, never official product values.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs/replay/pandar_skew_journey_2026-09-06"
OUTPUT = ROOT / "outputs/pandar_hypothesis_2026-09-07"
RANK_WINDOW = 252
RANK_MINIMUM = 100
EXTREME_RETURN = .25
ADJUSTMENT_DIVERGENCE = .05
SUMMARY_COLUMNS = ["ticker", "tradeDate", "stockPrice", "iv30d", "iv60d",
                   "dlt25Iv30d", "dlt75Iv30d"]
DAILY_COLUMNS = ["ticker", "tradeDate", "clsPx", "unadjClsPx"]
CONTRACT_COLUMNS = ["ticker", "tradeDate", "selection_status", "expiry", "far_strike",
                    "near_strike", "signal_delta", "signal_near_delta", "signal_otm_pct",
                    "signal_spot", "signal_calendar_dte"]


def _series(values: pd.Series) -> pd.Series:
    result = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)
    result.index = pd.DatetimeIndex(pd.to_datetime(result.index)).normalize()
    if result.index.has_duplicates:
        raise ValueError("duplicate observation dates")
    return result.sort_index()


def _calendar(dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    result = pd.DatetimeIndex(pd.to_datetime(dates)).normalize().sort_values()
    if result.has_duplicates:
        raise ValueError("duplicate session dates")
    return result


def rank_at_signal(values: pd.Series, sessions: pd.DatetimeIndex,
                   signal: pd.Timestamp) -> dict[str, Any]:
    """Rank against actual prior session slots, excluding current values and ties."""
    values, sessions, signal = _series(values), _calendar(sessions), pd.Timestamp(signal)
    prior_dates = sessions[sessions < signal][-RANK_WINDOW:]
    prior = values.reindex(prior_dates).dropna()
    current = values.get(signal, np.nan)
    enough = len(prior) >= RANK_MINIMUM
    rank = float((prior < current).mean()) if enough and pd.notna(current) else None
    status = "current_unavailable" if pd.isna(current) else (
        "ok" if enough else "insufficient_prior_history"
    )
    return {"rank_01": rank, "rank_pct": None if rank is None else 100 * rank,
            "n": len(prior), "missing_prior": len(prior_dates) - len(prior), "status": status,
            "window_sessions": len(prior_dates), "lookback_sessions": RANK_WINDOW,
            "minimum_valid": RANK_MINIMUM,
            "first_prior_session": prior_dates[0].strftime("%Y-%m-%d") if len(prior_dates) else None,
            "last_prior_session": prior_dates[-1].strftime("%Y-%m-%d") if len(prior_dates) else None}


def realized_at_signal(adjusted: pd.Series, unadjusted: pd.Series,
                       sessions: pd.DatetimeIndex, signal: pd.Timestamp,
                       days: int) -> dict[str, Any]:
    """Annualize all squared adjusted log returns in (signal-days, signal], retaining jumps."""
    signal = pd.Timestamp(signal)
    calendar = _calendar(sessions)
    calendar = calendar[calendar <= signal]
    adj = _series(adjusted).reindex(calendar).where(lambda x: x > 0)
    raw = _series(unadjusted).reindex(calendar).where(lambda x: x > 0)
    boundary = signal - pd.Timedelta(days=days)
    window = calendar[calendar > boundary]
    returns = np.log(adj / adj.shift(1)).reindex(window)
    adj_simple = (adj / adj.shift(1) - 1).reindex(window)
    raw_simple = (raw / raw.shift(1) - 1).reindex(window)
    divergence = (adj_simple - raw_simple).abs()
    complete = bool(len(calendar) and calendar[0] <= boundary and len(window)
                    and returns.notna().all() and signal in window)
    rv = float(np.sqrt(252 * returns.pow(2).mean())) if complete else None
    extreme = adj_simple.abs() >= EXTREME_RETURN
    adjustments = divergence > ADJUSTMENT_DIVERGENCE
    flags = []
    if extreme.any():
        flags.append("extreme_adjusted_jump")
    if adjustments.any():
        flags.append("adjusted_unadjusted_divergence")
    if raw_simple.isna().any():
        flags.append("unadjusted_comparison_incomplete")
    return {"rv_decimal": rv, "rv_pct": None if rv is None else 100 * rv,
            "status": "ok_reported_adjusted_prices" if complete else "incomplete_return_window",
            "calendar_days": days, "n_returns": int(returns.notna().sum()),
            "expected_returns": len(window), "price_quality": ";".join(flags) or "no_threshold_flag",
            "extreme_adjusted_jump_count": int(extreme.sum()),
            "extreme_adjusted_jump_dates": ";".join(window[extreme].strftime("%Y-%m-%d")),
            "adjusted_unadjusted_divergence_count": int(adjustments.sum()),
            "adjustment_divergence_dates": ";".join(window[adjustments].strftime("%Y-%m-%d")),
            "max_abs_adjusted_return_pct": float(adj_simple.abs().max() * 100),
            "max_abs_unadjusted_return_pct": float(raw_simple.abs().max() * 100)}


def _normalize(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    if not {"ticker", "tradeDate"} <= set(frame):
        raise ValueError(f"{label} missing ticker/tradeDate")
    frame = frame.copy()
    frame["tradeDate"] = pd.to_datetime(frame.tradeDate).dt.normalize()
    if frame[["ticker", "tradeDate"]].isna().any().any():
        raise ValueError(f"{label} has missing join keys")
    if frame.duplicated(["ticker", "tradeDate"]).any():
        raise ValueError(f"{label} has duplicate ticker/date keys")
    return frame


def _column(frame: pd.DataFrame, column: str, *, positive: bool = False) -> pd.Series:
    values = pd.to_numeric(frame.get(column, pd.Series(np.nan, index=frame.index)), errors="coerce")
    values = values.replace([np.inf, -np.inf], np.nan)
    return values.where(values > 0) if positive else values


def _fmt(value: Any, decimals: int = 1) -> str:
    return "unavailable" if pd.isna(value) else f"{value:.{decimals}f}"


def enrich_population(population: pd.DataFrame, summaries: pd.DataFrame,
                      dailies: pd.DataFrame, contracts: pd.DataFrame) -> pd.DataFrame:
    """Return exactly the frozen cases in original order, including missing option selections."""
    population = _normalize(population, "population")
    summaries = _normalize(summaries, "summaries")
    dailies = _normalize(dailies, "dailies")
    contracts = _normalize(contracts, "contracts")
    calendar = _calendar(pd.DatetimeIndex(dailies.loc[dailies.ticker.eq("SPY"), "tradeDate"]))
    if calendar.empty:
        raise ValueError("SPY session calendar unavailable; do not substitute business days")
    contract_lookup = contracts.set_index(["ticker", "tradeDate"]).to_dict("index")
    result = []
    for pop in population.to_dict("records"):
        ticker, signal = pop["ticker"], pop["tradeDate"]
        summary = summaries[summaries.ticker.eq(ticker)].set_index("tradeDate").sort_index()
        daily = dailies[dailies.ticker.eq(ticker)].set_index("tradeDate").sort_index()
        iv30 = _column(summary, "iv30d", positive=True)
        iv60 = _column(summary, "iv60d", positive=True)
        call25 = _column(summary, "dlt25Iv30d", positive=True)
        put25 = _column(summary, "dlt75Iv30d", positive=True)
        rr30 = call25 - put25
        contract = contract_lookup.get((ticker, signal), {})
        row: dict[str, Any] = {
            "signal_id": pop.get("signal_id"), "ticker": ticker,
            "signal_date": signal.strftime("%Y-%m-%d"), "entry_date": pop.get("entry_date"),
            "population_selection_status": pop.get("selection_status"),
            "contract_selection_status": contract.get("selection_status", "contract_record_missing"),
            "rank_product_label": "SpotGamma-compatible ORATS reconstruction; not official values",
            "rank_method": "30D_input_prior_252_exchange_sessions_min100_strict_below_exclude_current",
            "iv30_decimal": iv30.get(signal, np.nan), "iv30_pct": 100 * iv30.get(signal, np.nan),
            "iv60_decimal": iv60.get(signal, np.nan), "iv60_pct": 100 * iv60.get(signal, np.nan),
            "rr30_vol_points": 100 * rr30.get(signal, np.nan),
            "call25_minus_atm30_vol_points": 100 * (call25 - iv30).get(signal, np.nan),
            "put25_minus_atm30_vol_points": 100 * (put25 - iv30).get(signal, np.nan),
        }
        for name, values in (("iv30", iv30), ("rr30", rr30)):
            stats = rank_at_signal(values, calendar, signal)
            row.update({f"{name}_rank_{key}": value for key, value in stats.items()
                        if key not in {"rank_01", "rank_pct"}})
            row[f"{name}_rank_01"], row[f"{name}_rank_pct"] = stats["rank_01"], stats["rank_pct"]
        for days, implied in ((30, iv30), (60, iv60)):
            stats = realized_at_signal(_column(daily, "clsPx"), _column(daily, "unadjClsPx"),
                                       calendar, signal, days)
            row.update({f"rv{days}_{key}": value for key, value in stats.items()})
            rv = stats["rv_decimal"]
            current_iv = implied.get(signal, np.nan)
            row[f"variance_premium{days}_recomputed"] = (
                current_iv ** 2 - rv ** 2 if rv is not None and pd.notna(current_iv) else np.nan
            )
            old_rv = pop.get(f"rv{days}", np.nan)
            row[f"frozen_rv{days}_decimal"] = old_rv
            row[f"rv{days}_minus_frozen"] = rv - old_rv if rv is not None else np.nan
        row["rv_method"] = "252_mean_squared_log_returns_reported_clsPx_complete_calendar_window"
        row["variance_premium_units"] = "annualized_decimal_variance"
        row["rv_price_basis"] = "ORATS_reported_adjusted_clsPx_not_independently_corporate_action_verified"
        row["signal_adjusted_close"] = _column(daily, "clsPx").get(signal, np.nan)
        row["signal_unadjusted_close"] = _column(daily, "unadjClsPx").get(signal, np.nan)
        summary_spot = _column(summary, "stockPrice").get(signal, np.nan)
        row["signal_summary_spot"] = summary_spot
        raw_close = row["signal_unadjusted_close"]
        row["summary_to_unadjusted_close_gap_pct"] = (
            100 * (summary_spot / raw_close - 1) if pd.notna(raw_close) and raw_close > 0 else np.nan
        )
        row["iv_input_review"] = ";".join(
            f"{name}_at_least_500pct_review" for name, values in
            (("iv30", iv30), ("iv60", iv60), ("call25", call25), ("put25", put25))
            if values.get(signal, np.nan) >= 5
        ) or "no_extreme_input_threshold_flag"
        proxy_map = {
            "wing": "call_wing_5delta_10d_vol_points", "wing_rank": "call_wing_proxy_rank_pct",
            "age": "wing_observed_age_sessions", "left_censored": "wing_age_left_censored",
            "intensity": "wing_cumulative_normalized_rank_excess",
            "peak_minus_wing": "wing_pullback_from_known_peak_vol_points",
            "rolling_over": "wing_rollover_two_sessions", "expanding": "wing_expanding_two_sessions",
            "wing_slope": "wing_slope_vol_points_per_session",
            "wing_acceleration": "wing_second_difference_vol_points",
            "iv10_slope": "iv10_slope_vol_points_per_session",
            "iv10_acceleration": "iv10_second_difference_vol_points",
            "callskew30": "call_skew_exearn_25delta_30d_vol_points",
            "callskew30_rank": "call_skew_exearn_25delta_proxy_rank_pct",
            "confidence_pct": "surface_confidence_pct", "dollar_turnover20": "dollar_turnover20",
        }
        row.update({label: pop.get(source, np.nan) for source, label in proxy_map.items()})
        row["wing_depth_above_rank85_points"] = pop.get("wing_rank", np.nan) - 85
        row["proxy_rank_method"] = "frozen_252_session_min126_strict_below_not_Compass_IV_or_RR"
        for key in CONTRACT_COLUMNS:
            if key not in {"ticker", "tradeDate", "selection_status"}:
                row[key] = contract.get(key, np.nan)
        row["signal_delta_points"] = 100 * row["signal_delta"]
        row["why_qualified"] = (
            f"Frozen HIRO stock with {_fmt(pop.get('wing_rank', np.nan))}th-percentile positive "
            f"front call wing ({_fmt(pop.get('wing', np.nan))} volatility points), "
            f"{_fmt(pop.get('confidence_pct', np.nan))}% surface confidence and "
            f"${_fmt(pop.get('dollar_turnover20', np.nan) / 1e6)}m daily dollar turnover; "
            "passed the retrospective 30-day earnings and nonoverlap gates with an entry-day "
            f"HIRO archive; contract status: {row['contract_selection_status']}."
        )
        result.append(row)
    output = pd.DataFrame(result)
    if len(output) != len(population):
        raise AssertionError("descriptive enrichment changed the frozen population")
    return output


def _definitions(frame: pd.DataFrame, sources: list[Path]) -> str:
    """Document exact research conventions, source hashes and observed support."""
    lines = [
        "# Frozen population descriptive features", "",
        f"All {len(frame)} frozen rows are retained, including "
        f"{int(frame.contract_selection_status.ne('selected').sum())} unselected contracts. "
        "This enrichment changes no population gate, contract, hypothesis, or protocol. "
        "No provider requests or option outcome inputs are used.", "",
        "## IV Rank and Risk Reversal Rank", "",
        "The authoritative local SpotGamma learnings reference supersedes the older Compass "
        "skill's 90-day-input reconstruction. These columns are **SpotGamma-compatible ORATS "
        "reconstructions**, not exact official product values or calibrated live hover cards.", "",
        "- IV input: raw 30-calendar-day ATM IV `iv30d` in decimal volatility.",
        "- Risk reversal: `dlt25Iv30d - dlt75Iv30d`, 30-day 25-delta call minus 25-delta put IV. "
        "Negative RR is valid. High RR rank describes calls richer relative to puts in their own "
        "history; it does not establish an absolute expensive call.",
        "- Decomposition: call25-minus-ATM and put25-minus-ATM are shown separately in volatility "
        "points. Their difference equals RR. Neither leg uses ex-earnings IV.",
        "- Rank: share of valid values strictly below current in the preceding 252 SPY exchange "
        "sessions, excluding current. Minimum 100 valid dates. Missing sessions occupy window "
        "slots; no backward extension to accumulate 252 valid values. Ties count as not below. "
        "Missing/insufficient values remain unavailable, never zero.",
        "- `_rank_01` is a fraction; `_rank_pct` is exactly 100 times that fraction. This is a "
        "percentile, not the min-max statistic sometimes also called IV Rank.",
        "- Each rank exposes valid count, missing count, actual window size, start/end dates, "
        "lookback, minimum and status. 252 sessions and minimum 100 are project conventions, "
        "not publicly documented SpotGamma edge-case rules.", "",
        "Definition evidence was consulted locally: "
        "[SpotGamma learnings reference](/Users/dgrissen/.codex/skills/spotgamma-learnings/REFERENCE.md). "
        "It records the [official Guided View description](https://support.spotgamma.com/hc/en-us/"
        "articles/39936624524691-What-is-Guided-View-in-Compass) and first-party one-month webinar "
        "captures; no network fetch was performed for this enrichment.", "",
        "## Existing call-wing and call-skew proxies", "",
        "The frozen population used 5-call-delta/10-day IV minus ATM IV10, positive in absolute "
        "terms and at least the 85th prior percentile. Its saved rank uses 252 prior sessions "
        "and minimum 126. It is not IV30 Rank, RR30 Rank, an exact option bid-IV history or a "
        "claim that delta estimates touch probability.", "",
        "The separate saved call-skew measure is ex-earnings 30-day 25-delta call IV minus "
        "ex-earnings ATM IV. It is neither call-minus-put RR nor an official Compass fixed-"
        "moneyness skew value. The source proxy values are retained unchanged.", "",
        "Journey fields retain observed episode age and its left-censor flag, current percentile "
        "depth above 85, cumulative sum of `(rank-85)/15`, decline from the peak known at signal, "
        "two completed sessions of rollover/expansion, slopes and second differences. These "
        "describe different aspects of the journey; none was fitted to later option profits.", "",
        "## Realized volatility and price-quality flags", "",
        "For 30 and 60 **calendar days**, use all adjusted-close log returns ending in "
        "`(signal-days, signal]`, including the signal close. RV is "
        "`sqrt(252 * mean(log_return^2))`, a zero-drift historical estimate. It is not the "
        "Compass 20-trading-day realized-volatility display. Every expected return and its "
        "preceding price must exist; missing data prevents the RV estimate. The input is "
        "ORATS's reported adjusted `clsPx`; corporate-action correctness is not independently "
        "certified by the column name.", "",
        "A daily adjusted simple return of absolute magnitude at least 25% is flagged. A gap "
        "greater than five percentage points between adjusted and unadjusted daily simple "
        "returns is flagged separately. Missing unadjusted comparisons are explicit. These "
        "fixed audit thresholds are not trading filters or proof of an error: legitimate "
        "splits, dividends and market jumps require context. **No extreme return is deleted "
        "or winsorized.** RV values, valid/expected return counts, flag dates and largest daily "
        "moves remain available for review. `no_threshold_flag` means only that these checks "
        "did not fire, not verified data quality.", "",
        "Implied-minus-realized variance is `iv30d^2 - RV30^2` and `iv60d^2 - RV60^2`, in "
        "annualized decimal variance. Raw implied variance is compared with raw realized "
        "variance, not an asserted event-free diffusion premium or a forecast. Frozen RV "
        "values and recomputation differences are shown for reconciliation.", "",
        "IV inputs are decimals; display volatility percentages and volatility-point "
        "differences multiply by 100 once. Current IV values at least 5.0 (500%) receive "
        "an extreme-input/unit-review flag but are not silently rescaled or deleted. "
        "Nonpositive or nonfinite individual IV inputs cannot form a valid IV/RR measure.", "",
        "Signal summary spot, reported adjusted/unadjusted closes and their price gap are "
        "shown separately. Different snapshot times can explain a gap; prices are not "
        "silently spliced. Contract delta and OTM come from the frozen signal-date chain: "
        "delta fraction, delta points = 100*delta, OTM percent = 100*(K/S-1). Missing expiry "
        "or contract data remains missing. These are signal coordinates, not actual-entry Greeks.", "",
        "## Observed coverage", "",
        f"- IV30 rank available: {int(frame.iv30_rank_pct.notna().sum())}/{len(frame)}; "
        f"RR30 rank available: {int(frame.rr30_rank_pct.notna().sum())}/{len(frame)}.",
    ]
    for days in (30, 60):
        lines.append(f"- RV{days} available: {int(frame[f'rv{days}_rv_decimal'].notna().sum())}/"
                     f"{len(frame)}; rows with extreme adjusted jumps: "
                     f"{int(frame[f'rv{days}_extreme_adjusted_jump_count'].gt(0).sum())}; "
                     f"rows with adjusted/unadjusted divergence: "
                     f"{int(frame[f'rv{days}_adjusted_unadjusted_divergence_count'].gt(0).sum())}.")
    lines.extend(["", "## Reproduction and source hashes", "",
                  "`/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python "
                  "scripts/pandar_hypothesis_features.py`", "",
                  "The parquet reader projects only summary/price fields and filters dates "
                  "through the latest frozen signal. Each case then uses its own causal cutoff. "
                  "No derived-outcome panel is opened.", ""])
    for path in sources:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"- [{path.name}]({path.resolve()}): `{digest}`")
    return "\n".join(lines) + "\n"


def run() -> pd.DataFrame:
    """Read existing local caches and write only descriptive CSV and definitions."""
    population_path = OUTPUT / "selected_population.csv"
    contracts_path = OUTPUT / "frozen_contract_selections.csv"
    summary_path, daily_path = RESEARCH / "summaries.parquet", RESEARCH / "dailies.parquet"
    population = pd.read_csv(population_path)
    contracts = pd.read_csv(contracts_path, usecols=lambda c: c in CONTRACT_COLUMNS)
    cutoff = pd.Timestamp(population.tradeDate.max())
    names = sorted(set(population.ticker) | {"SPY"})
    filters = [("tradeDate", "<=", cutoff), ("ticker", "in", names)]
    summaries = pd.read_parquet(summary_path, columns=SUMMARY_COLUMNS, filters=filters)
    dailies = pd.read_parquet(daily_path, columns=DAILY_COLUMNS, filters=filters)
    result = enrich_population(population, summaries, dailies, contracts)
    result.to_csv(OUTPUT / "eligibility_features.csv", index=False)
    sources = [population_path, contracts_path, summary_path, daily_path, Path(__file__)]
    (OUTPUT / "feature_definitions.md").write_text(_definitions(result, sources), encoding="utf-8")
    return result


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    output = run()
    print(f"Wrote {len(output)} descriptive rows; IV30 ranks={output.iv30_rank_pct.notna().sum()}, "
          f"RR30 ranks={output.rr30_rank_pct.notna().sum()}")
