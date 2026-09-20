"""Boundary checks for mutually exclusive outcome categories and whole-day deletion."""

import unittest

import pandas as pd

from stability import classify, day_deletions


class StabilityTests(unittest.TestCase):
    def test_winner_does_not_become_endpoint_loss(self) -> None:
        self.assertEqual(classify("target_first", -20.0), "wins")
        self.assertEqual(classify("adverse_first", 3.0), "stops")

    def test_bucket_boundaries_and_zero(self) -> None:
        expected = {
            -9.0: "neg10_7_5",
            -7.5: "neg7_5_5",
            -5.0: "neg5_2_5",
            -2.5: "neg2_5_0",
            0.0: "flat",
            1.0: "pos0_2_5",
            2.5: "pos2_5_5",
        }
        for value, category in expected.items():
            self.assertEqual(classify("neither", value), category)
        for value in [-10.0, 5.0, float("nan")]:
            with self.assertRaises(ValueError):
                classify("neither", value)

    def test_remove_whole_day_and_recount_denominator(self) -> None:
        frame = pd.DataFrame(
            {
                "date": ["a"] * 4 + ["b"] * 2,
                "category": ["wins", "wins", "wins", "stops", "wins", "flat"],
            }
        )
        result = day_deletions(frame, ["a", "b", "c"]).set_index("removed_date")
        self.assertEqual(result.loc["a", "remaining_n"], 2)
        self.assertEqual(result.loc["a", "wins_pct"], 50.0)
        self.assertEqual(result.loc["b", "remaining_n"], 4)
        self.assertEqual(result.loc["b", "wins_pct"], 75.0)
        self.assertEqual(result.loc["c", "remaining_n"], 6)
        self.assertAlmostEqual(result.loc["c", "wins_pct"], 100 * 4 / 6)

    def test_empty_remainder_has_unknown_rate(self) -> None:
        frame = pd.DataFrame({"date": ["a"], "category": ["wins"]})
        row = day_deletions(frame, ["a"]).iloc[0]
        self.assertEqual(row.remaining_n, 0)
        self.assertTrue(pd.isna(row.wins_pct))


if __name__ == "__main__":
    unittest.main()
