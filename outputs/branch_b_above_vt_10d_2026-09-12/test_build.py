"""Data-selection and aggregation checks for the entry carousel."""
import unittest

import pandas as pd

from build import aggregate_day, select_days


class DataContractTest(unittest.TestCase):
    def test_incomplete_and_duplicate_minutes_are_rejected(self) -> None:
        raw = pd.DataFrame({"min": range(570, 960), "open": 100.0,
                            "high": 102.0, "low": 99.0, "close": 101.0})
        bars = aggregate_day("2026-09-01", raw)
        self.assertEqual(len(bars), 78)
        self.assertEqual(bars.iloc[0]["min5"], 570)
        self.assertEqual(bars.iloc[-1]["min5"], 955)
        with self.assertRaises(ValueError):
            aggregate_day("2026-09-01", raw.drop(index=2))
        with self.assertRaises(ValueError):
            aggregate_day("2026-09-01", pd.concat([raw, raw.iloc[[2]]]))

    def test_selection_uses_open_and_recency_without_outcomes(self) -> None:
        rows = pd.DataFrame([
            {"date": "2026-09-01", "open": 101, "vt": 100, "complete": True},
            {"date": "2026-09-02", "open": 102, "vt": 100, "complete": True},
            {"date": "2026-09-03", "open": 100, "vt": 100, "complete": True},
            {"date": "2026-09-04", "open": 110, "vt": 100, "complete": False},
            {"date": "2026-09-08", "open": 101, "vt": 100, "complete": True},
        ])
        self.assertEqual(select_days(rows, 2)["date"].tolist(),
                         ["2026-09-02", "2026-09-08"])
        with self.assertRaises(ValueError):
            select_days(rows, 4)


if __name__ == "__main__":
    unittest.main()
