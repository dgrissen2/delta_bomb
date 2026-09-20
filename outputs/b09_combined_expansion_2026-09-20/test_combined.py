"""Boundary cases for the combined route ledger, independent of real outcomes."""

import unittest

import pandas as pd

from combined import aggregate_routes, attach_outcomes


def parent(identity: str, minute: int, **flags: bool) -> dict:
    return (
        dict(
            entry_id=identity,
            date="2025-01-06",
            known_min=minute,
            half="2025_H1",
            baseline=False,
            b05_candidate=False,
            persistence_candidate=False,
            b07_candidate=False,
        )
        | flags
    )


class CombinedTests(unittest.TestCase):
    def test_shared_minute_keeps_all_routes_once(self) -> None:
        frame = pd.DataFrame(
            [
                parent("b09", 615, baseline=True, persistence_candidate=True),
                parent("b05", 615, b05_candidate=True),
                parent("b07", 615, b07_candidate=True),
                parent("later", 625, persistence_candidate=True),
                parent("rejected", 626),
            ]
        )
        result = aggregate_routes(frame)
        self.assertEqual(result.known_min.tolist(), [615, 625])
        self.assertTrue(
            result.iloc[0][
                ["baseline", "b05_candidate", "persistence_candidate", "b07_candidate"]
            ].all()
        )
        self.assertFalse(result.iloc[0].added)
        self.assertTrue(result.iloc[1].added)

    def test_false_baseline_at_same_time_does_not_erase_true(self) -> None:
        frame = pd.DataFrame(
            [
                parent("b05", 615, b05_candidate=True),
                parent("b09", 615, baseline=True, persistence_candidate=True),
            ]
        )
        self.assertTrue(aggregate_routes(frame).iloc[0].baseline)

    def test_conflicting_duplicate_outcomes_fail(self) -> None:
        routes = aggregate_routes(pd.DataFrame([parent("b09", 615, baseline=True)]))
        rows = pd.DataFrame(
            [
                dict(
                    date="2025-01-06",
                    known_min=615,
                    entry_price=6000.0,
                    outcome="target_first",
                    first_touch_min=620,
                ),
                dict(
                    date="2025-01-06",
                    known_min=615,
                    entry_price=6000.0,
                    outcome="adverse_first",
                    first_touch_min=620,
                ),
            ]
        )
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            attach_outcomes(routes, rows)

    def test_missing_outcome_fails(self) -> None:
        routes = aggregate_routes(pd.DataFrame([parent("b09", 615, baseline=True)]))
        rows = pd.DataFrame(
            [
                dict(
                    date="2025-01-06",
                    known_min=616,
                    entry_price=6000.0,
                    outcome="target_first",
                    first_touch_min=620,
                ),
            ]
        )
        with self.assertRaisesRegex(ValueError, "Missing"):
            attach_outcomes(routes, rows)


if __name__ == "__main__":
    unittest.main()
