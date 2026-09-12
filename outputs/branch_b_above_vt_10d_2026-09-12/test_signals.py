"""Boundary, episode and causal-availability tests for the entry-only prototype."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from signals import add_features, evaluate_day


def fixture(mins: list[int] | None = None) -> pd.DataFrame:
    """Hand-specified features isolate admission rules from indicator smoothing."""
    if mins is None:
        mins = [585, 590, 595]
    n = len(mins)
    close = 9980.0 + 10.0 * np.arange(n)
    lips = close - 1.0
    gaps = 0.2 + 0.2 * np.arange(n)
    return pd.DataFrame({
        "date": ["2026-09-01"] * n,
        "min5": mins,
        "open": close - 6.0,
        "high": close + 1.0,
        "low": close - 7.0,
        "close": close,
        "lips": lips,
        "teeth": lips - gaps,
        "jaw": lips - 2.0 * gaps,
        "atr": np.full(n, 10.0),
        "adx": np.zeros(n),
    })


class SignalRulesTest(unittest.TestCase):
    def test_thrust_threshold_and_thrust_priority(self) -> None:
        bars = fixture()
        rows, events = evaluate_day(bars)
        self.assertEqual(rows.iloc[-1].break_bps, 10.0)
        self.assertTrue(rows.iloc[-1].thrust_raw)
        self.assertTrue(rows.iloc[-1].staircase_raw)
        self.assertEqual([e["variant"] for e in events], ["thrust", "staircase"])
        self.assertTrue(all(e["kind"] == "thrust" for e in events))
        bars.loc[2, "close"] -= 0.001
        rows, events = evaluate_day(bars)
        self.assertFalse(rows.iloc[-1].thrust_raw)
        self.assertEqual([e["variant"] for e in events], ["staircase"])

    def test_body_top_includes_prior_open_and_excludes_current_bar(self) -> None:
        bars = fixture()
        bars.loc[1, ["open", "high"]] = [10002.0, 10003.0]
        rows, events = evaluate_day(bars)
        self.assertEqual(rows.iloc[-1].prior_body_top, 10002.0)
        self.assertLess(rows.iloc[-1].break_bps, 0)
        self.assertEqual(events, [])

    def test_fan_threshold_and_strict_gap_expansion(self) -> None:
        bars = fixture()
        bars.loc[2, "teeth"] = bars.loc[2, "lips"] - 0.5
        bars.loc[2, "jaw"] = bars.loc[2, "lips"] - 1.0
        rows, _ = evaluate_day(bars)
        self.assertTrue(rows.iloc[-1].common_ok)
        bars.loc[2, "jaw"] += 0.001
        rows, _ = evaluate_day(bars)
        self.assertFalse(rows.iloc[-1].common_ok)
        bars = fixture()
        gap = bars.loc[1, "lips"] - bars.loc[1, "teeth"]
        bars.loc[2, "teeth"] = bars.loc[2, "lips"] - gap
        rows, _ = evaluate_day(bars)
        self.assertFalse(rows.iloc[-1].common_ok)

    def test_extension_boundary_and_no_adx_gate(self) -> None:
        bars = fixture()
        bars.loc[2, ["lips", "teeth", "jaw"]] -= 14.0
        rows, events = evaluate_day(bars)
        self.assertEqual(rows.iloc[-1].ext_atr, 1.5)
        self.assertTrue(rows.iloc[-1].common_ok)
        self.assertEqual(len(events), 2)
        bars.loc[2, ["lips", "teeth", "jaw"]] -= 0.001
        rows, events = evaluate_day(bars)
        self.assertFalse(rows.iloc[-1].common_ok)
        self.assertEqual(events, [])

    def test_staircase_slope_and_strict_solid_green(self) -> None:
        bars = fixture()
        bars.loc[1, ["open", "high", "low", "close"]] = [9993, 9997, 9992, 9996]
        bars.loc[0, "lips"] = bars.loc[2, "lips"] - 6
        bars.loc[0, "teeth"] = bars.loc[0, "lips"] - 0.2
        bars.loc[0, "jaw"] = bars.loc[0, "lips"] - 0.4
        rows, events = evaluate_day(bars)
        self.assertEqual(rows.iloc[-1].slope2_atr, 0.6)
        self.assertTrue(rows.iloc[-1].staircase_raw)
        self.assertEqual([e["variant"] for e in events], ["staircase"])
        bars.loc[0, "lips"] += 0.001
        rows, events = evaluate_day(bars)
        self.assertFalse(rows.iloc[-1].staircase_raw)
        self.assertEqual(events, [])
        bars.loc[0, "lips"] -= 0.001
        bars.loc[1, "low"] = 9991.0  # Body == sum of wicks is not solid green.
        rows, events = evaluate_day(bars)
        self.assertFalse(rows.iloc[-1].staircase_raw)
        self.assertEqual(events, [])

    def test_contiguous_runs_rearm_and_staircase_bridge(self) -> None:
        bars = fixture([585, 590, 595, 600, 605, 610, 615])
        # At 10:05, staircase qualifies while thrust misses; that bridges the enabled run.
        bars.loc[3, ["open", "high", "low", "close"]] = [10002, 10009, 10001, 10008]
        # At 10:15 neither package qualifies, so both rearm for 10:20.
        bars.loc[5, "open"] = bars.loc[5, "close"]
        bars.loc[6, ["open", "high", "low", "close"]] += 2.0  # >10 bp at the higher level.
        rows, events = evaluate_day(bars)
        self.assertFalse(rows.loc[3, "thrust_ok"])
        self.assertTrue(rows.loc[3, "staircase_ok"])
        self.assertEqual(
            [e["known_min"] for e in events if e["variant"] == "thrust"],
            [600, 610, 620],
        )
        self.assertEqual(
            [e["known_min"] for e in events if e["variant"] == "staircase"],
            [600, 620],
        )

    def test_completed_bar_clock_and_window_reset(self) -> None:
        bars = fixture([575, 580, 585, 590, 595, 600])
        _, events = evaluate_day(bars)
        self.assertEqual({e["known_min"] for e in events}, {600})
        self.assertEqual({e["signal_min"] for e in events}, {595})
        bars = fixture([855, 860, 865, 870, 875])
        _, events = evaluate_day(bars)
        self.assertEqual({e["known_min"] for e in events}, {870})
        bars = fixture([595, 600])
        self.assertEqual(evaluate_day(bars)[1], [])

    def test_invalid_atr_cannot_create_signal(self) -> None:
        for atr in [0.0, float("nan"), float("inf")]:
            with self.subTest(atr=atr):
                bars = fixture()
                bars.loc[2, "atr"] = atr
                self.assertEqual(evaluate_day(bars)[1], [])


class FeatureAvailabilityTest(unittest.TestCase):
    def test_continuous_ema_and_overnight_true_range(self) -> None:
        bars = pd.DataFrame({
            "date": ["2026-09-01", "2026-09-02"], "min5": [955, 570],
            "open": [100.0, 110.0], "high": [101.0, 111.0],
            "low": [99.0, 109.0], "close": [100.0, 110.0],
        })
        rows = add_features(bars)
        self.assertAlmostEqual(rows.loc[1, "lips"], 100 + 10 / 3)
        self.assertEqual(rows.loc[1, "tr"], 11.0)
        self.assertAlmostEqual(rows.loc[1, "atr"], 2 + 9 / 14)
        self.assertAlmostEqual(rows.loc[1, "adx"], 100 / 14)

    def test_appending_future_data_cannot_change_history(self) -> None:
        n = 160
        close = 10000 + np.arange(n) * 0.35 + np.sin(np.arange(n) / 3)
        bars = pd.DataFrame({
            "date": ["2026-09-01"] * 78 + ["2026-09-02"] * 78
                    + ["2026-09-03"] * 4,
            "min5": [570 + 5 * (i % 78) for i in range(n)],
            "open": close - 0.5, "high": close + 0.1,
            "low": close - 0.6, "close": close,
        })
        short = add_features(bars.iloc[:125])
        full = add_features(bars)
        assert_frame_equal(short, full.iloc[:125])
        prior_rows, prior_events = evaluate_day(short[short.date == "2026-09-02"])
        full_rows, full_events = evaluate_day(full[full.date == "2026-09-02"])
        self.assertGreater(len(prior_events), 0)
        assert_frame_equal(prior_rows, full_rows.iloc[:len(prior_rows)])
        last_known = int(prior_rows.iloc[-1].known_min)
        self.assertEqual(prior_events, [e for e in full_events if e["known_min"] <= last_known])

    def test_reject_unsorted_duplicate_or_multiple_day_input(self) -> None:
        bars = fixture()
        with self.assertRaises(ValueError):
            add_features(bars.iloc[::-1])
        with self.assertRaises(ValueError):
            add_features(pd.concat([bars, bars.iloc[-1:]]))
        bars.loc[2, "date"] = "2026-09-02"
        with self.assertRaises(ValueError):
            evaluate_day(bars)


if __name__ == "__main__":
    unittest.main()
