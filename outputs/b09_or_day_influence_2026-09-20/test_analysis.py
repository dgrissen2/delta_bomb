"""Small hand-calculated checks of the day-removal arithmetic."""

import math
import unittest

import pandas as pd

from analyze import daily_counts, leave_one_out


class DayInfluenceTests(unittest.TestCase):
    def test_counts_keep_zero_days_and_non_target_outcomes(self) -> None:
        events = pd.DataFrame({
            "date": ["a", "a", "a", "b"],
            "outcome": ["target_first", "adverse_first", "ambiguous", "neither"],
        })
        daily = daily_counts(events, ["a", "b", "c"])
        self.assertEqual(daily.n.tolist(), [3, 1, 0])
        self.assertEqual(daily.target_first.tolist(), [1, 0, 0])
        self.assertEqual(daily.ambiguous.tolist(), [1, 0, 0])
        loo = leave_one_out(daily)
        self.assertEqual(loo.remaining_n.tolist(), [1, 3, 4])
        self.assertAlmostEqual(loo.iloc[1].remaining_rate, 100 / 3)
        self.assertAlmostEqual(loo.iloc[2].remaining_rate, 25)
        self.assertAlmostEqual(loo.iloc[0].delta_pp, -25)

    def test_removing_only_active_day_is_undefined(self) -> None:
        daily = daily_counts(pd.DataFrame({"date": ["a"], "outcome": ["target_first"]}),
                             ["a", "b"])
        loo = leave_one_out(daily)
        self.assertTrue(math.isnan(loo.iloc[0].remaining_rate))
        self.assertEqual(loo.iloc[1].remaining_rate, 100)

    def test_unknown_outcome_fails(self) -> None:
        with self.assertRaises(ValueError):
            daily_counts(pd.DataFrame({"date": ["a"], "outcome": ["unknown"]}), ["a"])

    def test_unlisted_event_day_fails(self) -> None:
        with self.assertRaises(ValueError):
            daily_counts(pd.DataFrame({"date": ["a"], "outcome": ["target_first"]}), ["b"])


if __name__ == "__main__":
    unittest.main()
