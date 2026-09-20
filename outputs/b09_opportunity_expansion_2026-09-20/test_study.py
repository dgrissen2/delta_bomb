"""Hand-calculated causal and execution-boundary checks."""

import unittest

import numpy as np
import pandas as pd

from study import persistence, rvol, unique, thin


class StudyTests(unittest.TestCase):
    def test_persistence_cannot_pool_different_times(self) -> None:
        m = np.zeros((1, 5, 4))
        m[0, 0, :2] = 2
        m[0, 1, 2:] = 2
        b = np.full_like(m, -0.1)
        state, witness = persistence(m, b, 4)
        self.assertEqual(state.tolist(), ["no"])
        self.assertEqual(witness.tolist(), [-1])

    def test_current_falling_must_be_same_sectors(self) -> None:
        m = np.zeros((1, 5, 5))
        m[0, 0, :4] = 2
        b = np.full_like(m, -0.1)
        b[0, -1, 0] = 0.1
        self.assertEqual(persistence(m, b, 4)[0].tolist(), ["no"])

    def test_unknown_current_slope_is_not_falling(self) -> None:
        m = np.ones((1, 5, 4)) * 2
        b = np.full_like(m, -0.1)
        b[0, -1, 0] = np.nan
        self.assertEqual(persistence(m, b, 4)[0].tolist(), ["unknown"])

    def test_current_qualifier_survives_and_earliest_witness(self) -> None:
        m = np.zeros((1, 5, 4))
        m[0, -1] = 2
        b = np.full_like(m, -0.1)
        self.assertEqual(persistence(m, b, 4)[0].tolist(), ["yes"])
        self.assertEqual(persistence(m, b, 4)[1].tolist(), [4])
        m[0, 1] = 2
        self.assertEqual(persistence(m, b, 4)[1].tolist(), [1])

    def test_unknown_old_endpoint_does_not_erase_current_yes(self) -> None:
        m = np.full((1, 5, 1), np.nan)
        b = m.copy()
        m[0, -1, 0] = 2
        b[0, -1, 0] = -0.1
        self.assertEqual(persistence(m, b, 1)[0].tolist(), ["yes"])

    def test_rvol_uses_prior_dates_only_and_requires_all_60(self) -> None:
        matrix = pd.DataFrame({599: [10.0] * 60 + [30.0, 1000.0]}, index=range(62))
        self.assertEqual(rvol(matrix, 60, 600)[0], 3.0)
        self.assertEqual(rvol(matrix, 59, 600)[2], "insufficient_history")
        matrix.loc[3, 599] = np.nan
        self.assertTrue(np.isnan(rvol(matrix, 60, 600)[0]))
        self.assertEqual(rvol(matrix, 60, 600)[2], "incomplete_history")

    def test_dedup_rejects_conflicting_outcome(self) -> None:
        e = pd.DataFrame(
            {
                "date": ["a", "a"],
                "known_min": [600, 600],
                "outcome": ["target_first", "adverse_first"],
            }
        )
        with self.assertRaises(ValueError):
            unique(e)

    def test_union_spacing_can_displace_base(self) -> None:
        e = pd.DataFrame(
            {"date": ["a", "a", "a", "b"], "known_min": [600, 610, 660, 600]}
        )
        self.assertEqual(thin(e, "spaced60").known_min.tolist(), [600, 660, 600])
        self.assertEqual(thin(e, "first").known_min.tolist(), [600, 600])


if __name__ == "__main__":
    unittest.main()
