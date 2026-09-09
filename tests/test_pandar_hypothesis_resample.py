"""The frozen five-session block cannot manufacture independent economic evidence."""

import numpy as np
import pandas as pd
import pytest

from scripts.pandar_hypothesis_resample import comparison_pairs, resample_comparisons


DAYS = ["2026-06-12", "2026-06-15", "2026-06-16", "2026-06-17", "2026-06-18"]


def replay_rows():
    rows = []
    for index, day in enumerate(DAYS):
        # Unequal cross-sections must travel intact with their date.
        for ticker in ["A", "B"] if index == 0 else ["A"]:
            for policy in ("clock", "hiro"):
                for horizon in (4, 5):
                    for cost in (.01, .02):
                        for method in ("immediate_spread", "deferred_d0", "deferred_d1", "deferred_d2", "short_only"):
                            pnl = {"immediate_spread": 1., "deferred_d0": 2., "deferred_d1": 3.,
                                   "deferred_d2": 4., "short_only": 5.}[method]
                            rows.append(dict(variant="original", ticker=ticker, signal_date=day,
                                             entry_date=day, entry_policy=policy, method=method,
                                             holding_sessions=horizon, slippage_per_share=cost,
                                             pnl_net=pnl + (1. if policy == "hiro" else 0.),
                                             cover_at_conversion_pnl=0.))
    return pd.DataFrame(rows)


def test_2000_draws_of_single_five_session_block_are_explicitly_degenerate():
    result = resample_comparisons(replay_rows(), DAYS)
    assert result["replicates"] == 2000
    assert result["complete_five_session_blocks"] == 1
    assert result["block_draw_counts"] == {"0": 2000}
    assert result["statistical_pass"] is False
    assert result["calendar"] == DAYS
    for group in result["comparisons"]:
        assert group["population_cases"] == group["paired_cases"] == 6
        assert group["confidence_interval"] is None
        assert group["bootstrap_unique_means"] == 1
        assert group["bootstrap_mean_quantiles"] == [group["mean_difference"]] * 2
        assert group["population_by_date"][DAYS[0]] == 2


def test_pairing_uses_exact_episode_and_retains_missing_pair_denominators():
    rows = replay_rows()
    target = rows.ticker.eq("B") & rows.method.eq("short_only") & rows.entry_policy.eq("clock")
    rows.loc[target, "pnl_net"] = np.nan
    result = resample_comparisons(rows, DAYS)
    selected = [group for group in result["comparisons"]
                if group["comparison"] == "deferred_d1_minus_short_only"
                and group["entry_policy"] == "clock"]
    assert len(selected) == 4
    assert all(group["population_cases"] == 6 and group["paired_cases"] == 5 for group in selected)
    assert all(group["mean_difference"] == -2 for group in selected)
    hiro = [group for group in result["comparisons"]
            if group["comparison"] == "hiro_minus_clock" and group["method"] == "short_only"]
    assert all(group["paired_cases"] == 5 for group in hiro)


def test_duplicate_episode_missing_policy_and_bad_calendar_fail_closed():
    rows = replay_rows()
    with pytest.raises(ValueError, match="duplicate"):
        comparison_pairs(pd.concat([rows, rows.iloc[:1]]))
    with pytest.raises(ValueError, match="40"):
        comparison_pairs(rows.iloc[1:])
    with pytest.raises(ValueError, match="chronological"):
        resample_comparisons(rows, DAYS[::-1])
    with pytest.raises(ValueError, match="five"):
        resample_comparisons(rows, DAYS[:4])
