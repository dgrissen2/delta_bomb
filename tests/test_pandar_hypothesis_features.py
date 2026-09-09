"""Descriptive enrichment keeps causal ranks, explicit units, and every frozen case."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pandar_hypothesis_features import enrich_population, rank_at_signal, realized_at_signal


def test_rank_is_prior_strict_below_percentile_not_minmax_or_current_inclusive():
    dates = pd.bdate_range("2025-01-01", periods=103)
    values = pd.Series([.2] * 50 + [.3] * 50 + [.3, 100, 200], index=dates)
    result = rank_at_signal(values, dates, dates[100])
    assert result["n"] == 100
    assert result["rank_01"] == .5 and result["rank_pct"] == 50
    values.iloc[101:] = -100
    assert rank_at_signal(values, dates, dates[100]) == result


def test_rank_uses_last_252_sessions_not_last_252_valid_values():
    dates = pd.bdate_range("2025-01-01", periods=300)
    values = pd.Series(np.arange(300, dtype=float), index=dates)
    values.iloc[-10:-1] = np.nan
    result = rank_at_signal(values, dates, dates[-1])
    assert result["window_sessions"] == 252 and result["n"] == 243
    assert result["first_prior_session"] == dates[-253].strftime("%Y-%m-%d")
    assert result["missing_prior"] == 9


def test_short_history_missing_current_and_duplicate_dates_are_explicit():
    dates = pd.bdate_range("2025-01-01", periods=100)
    values = pd.Series(.2, index=dates)
    result = rank_at_signal(values, dates, dates[-1])
    assert result["n"] == 99 and result["status"] == "insufficient_prior_history"
    assert result["rank_01"] is None
    values.iloc[-1] = np.nan
    assert rank_at_signal(values, dates, dates[-1])["status"] == "current_unavailable"
    with pytest.raises(ValueError, match="duplicate"):
        rank_at_signal(pd.concat([values, values.iloc[:1]]), dates, dates[-1])


def test_realized_vol_uses_complete_calendar_window_and_keeps_extreme_jump():
    dates = pd.bdate_range("2025-01-01", periods=80)
    adjusted = pd.Series(100., index=dates)
    adjusted.iloc[-1] = 150.
    result = realized_at_signal(adjusted, adjusted.copy(), dates, dates[-1], 30)
    expected_n = ((dates > dates[-1] - pd.Timedelta(days=30)) & (dates <= dates[-1])).sum()
    assert result["n_returns"] == expected_n
    assert result["rv_decimal"] == pytest.approx(np.sqrt(252 * np.log(1.5) ** 2 / expected_n))
    assert result["extreme_adjusted_jump_count"] == 1
    assert result["extreme_adjusted_jump_dates"] == dates[-1].strftime("%Y-%m-%d")
    assert "extreme_adjusted_jump" in result["price_quality"]
    adjusted.iloc[-3] = np.nan
    result = realized_at_signal(adjusted, adjusted.copy(), dates, dates[-1], 30)
    assert result["rv_decimal"] is None and result["status"] == "incomplete_return_window"


def test_adjustment_factor_change_is_flagged_without_deleting_adjusted_returns():
    dates = pd.bdate_range("2025-01-01", periods=80)
    adjusted = pd.Series(100., index=dates)
    unadjusted = adjusted.copy()
    unadjusted.iloc[-1] = 50.
    result = realized_at_signal(adjusted, unadjusted, dates, dates[-1], 60)
    assert result["rv_decimal"] == 0
    assert result["adjusted_unadjusted_divergence_count"] == 1
    assert "adjusted_unadjusted_divergence" in result["price_quality"]


def sample_inputs():
    dates = pd.bdate_range("2025-01-01", periods=130)
    signal = dates[-1]
    population = pd.DataFrame([
        {"ticker": ticker, "tradeDate": signal, "signal_id": f"{ticker}-{signal.date()}",
         "entry_date": "2025-07-02", "wing_rank": 90., "wing": 4., "age": 3,
         "left_censored": False, "intensity": 1., "peak_minus_wing": .4,
         "rolling_over": True, "expanding": False, "callskew30": 1.,
         "callskew30_rank": 75., "confidence_pct": 90., "dollar_turnover20": 3e7,
         "selected": True, "selection_status": "selected", "rv30": .1, "rv60": .2}
        for ticker in ("TEST", "NOEXP")
    ])
    summaries = pd.DataFrame([
        {"ticker": ticker, "tradeDate": day, "iv30d": .3 + i / 10000,
         "iv60d": .4, "dlt25Iv30d": .35 + i / 1000, "dlt75Iv30d": .4,
         "exErnDlt25Iv30d": 20., "stockPrice": 100.}
        for ticker in ("TEST", "NOEXP") for i, day in enumerate(dates)
    ])
    dailies = pd.DataFrame([
        {"ticker": ticker, "tradeDate": day, "clsPx": 100., "unadjClsPx": 100.}
        for ticker in ("TEST", "NOEXP", "SPY") for day in dates
    ])
    contracts = pd.DataFrame([
        {"ticker": "TEST", "tradeDate": signal, "selection_status": "selected",
         "signal_delta": .05, "signal_otm_pct": 10., "signal_calendar_dte": 10,
         "far_strike": 110., "near_strike": 105., "signal_spot": 100.},
        {"ticker": "NOEXP", "tradeDate": signal,
         "selection_status": "no_expiry_in_dte_band"},
    ])
    return population, summaries, dailies, contracts


def test_enrichment_rr_sign_decomposition_units_and_failed_contract_retention():
    population, summaries, dailies, contracts = sample_inputs()
    result = enrich_population(population, summaries, dailies, contracts)
    assert result.ticker.tolist() == ["TEST", "NOEXP"]
    row = result.iloc[0]
    assert row.rr30_vol_points == pytest.approx(7.9)
    assert row.call25_minus_atm30_vol_points - row.put25_minus_atm30_vol_points == pytest.approx(7.9)
    assert row.iv30_rank_01 == 1 and row.iv30_rank_pct == 100
    assert row.rr30_rank_01 == 1 and row.rr30_rank_pct == 100
    assert row.signal_delta == .05 and row.signal_delta_points == 5
    assert row.iv30_pct == pytest.approx(31.29)
    assert row.variance_premium30_recomputed == pytest.approx(.3129 ** 2)
    assert "SpotGamma-compatible" in row.rank_product_label
    assert result.iloc[1].contract_selection_status == "no_expiry_in_dte_band"
    assert pd.isna(result.iloc[1].signal_delta)
    assert "no_expiry_in_dte_band" in result.iloc[1].why_qualified


def test_missing_summary_retains_population_and_no_wrong_rr_proxy():
    population, summaries, dailies, contracts = sample_inputs()
    summaries = summaries[summaries.ticker.ne("NOEXP")].drop(columns="dlt75Iv30d")
    result = enrich_population(population, summaries, dailies, contracts)
    assert len(result) == len(population)
    assert result.rr30_rank_status.eq("current_unavailable").all()
    assert result.rr30_vol_points.isna().all()
    assert result.loc[result.ticker.eq("NOEXP"), "iv30_rank_status"].iloc[0] == "current_unavailable"


def test_enrichment_rejects_duplicate_join_keys():
    population, summaries, dailies, contracts = sample_inputs()
    with pytest.raises(ValueError, match="duplicate"):
        enrich_population(population, pd.concat([summaries, summaries.iloc[:1]]), dailies, contracts)
