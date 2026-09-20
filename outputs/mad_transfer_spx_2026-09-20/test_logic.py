"""Boundary tests for the reviewed rules; no strategy-selection tests."""
import unittest

import numpy as np
import pandas as pd

from logic import classify, endpoint_join, or_states, thin, within_blocks


class RulesTest(unittest.TestCase):
    def test_threshold_equality_and_four_votes(self):
        m = np.array([[2., 2., 2., 1.], [2., 2., 2., 1.01]])
        states, _, _ = classify(m, -m, -np.ones_like(m), "S4", breadth=4)
        self.assertEqual(states.tolist(), ["no", "yes"])

    def test_unknown_is_bounded_and_false_dominates(self):
        m = np.array([[2., 2., 2., np.nan], [2., 2., 2., np.nan]])
        b = np.array([[-1., -1., -1., np.nan], [-1., -1., -1., 0.]])
        states, yes, unknown = classify(m, -m, b, "F4", breadth=4)
        self.assertEqual(states.tolist(), ["unknown", "no"])
        self.assertEqual(yes.tolist(), [3, 3])
        self.assertEqual(unknown.tolist(), [1, 0])

    def test_missing_scale_cannot_supply_sign_vote(self):
        m = np.array([[np.nan]])
        self.assertEqual(classify(m, np.array([[-1.]]), np.array([[-1.]]),
                                  "sign4", breadth=1)[0].tolist(), ["unknown"])

    def test_falling_is_same_sector(self):
        m = np.array([[2., 2., 2., 2., 0., 0., 0., 0.]])
        b = np.array([[1., 1., 1., 1., -1., -1., -1., -1.]])
        self.assertEqual(classify(m, -m, b, "F4")[0].tolist(), ["no"])

    def test_sign_zero_is_not_negative(self):
        m = np.array([[0., 1.]])
        self.assertEqual(classify(m, -m, -np.ones_like(m), "sign4", breadth=2)[0]
                         .tolist(), ["no"])

    def test_or_three_valued_truth_table(self):
        a = np.array(["yes", "no", "unknown", "unknown", "no"])
        b = np.array(["unknown", "unknown", "yes", "unknown", "no"])
        self.assertEqual(or_states(a, b).tolist(),
                         ["yes", "unknown", "yes", "unknown", "no"])

    def test_endpoint_does_not_fill_from_future_or_nearby(self):
        e = pd.DataFrame({"date": ["d", "d"], "known_min": [600, 602]})
        s = pd.DataFrame({"date": ["d"], "end_min": [600], "value": [9.]})
        self.assertTrue(endpoint_join(e, s).value.isna().all())
        with self.assertRaises(ValueError):
            endpoint_join(e, pd.concat([s, s]))

    def test_spacing_boundary_and_reset(self):
        e = pd.DataFrame({"date": ["a"]*4 + ["b"],
                          "known_min": [600, 659, 660, 720, 600]})
        self.assertEqual(thin(e, "spaced60").index.tolist(), [0, 2, 3, 4])
        self.assertEqual(thin(e.iloc[1:], "spaced60").index.tolist(), [1, 3, 4])

    def test_within_blocks_weights_dates_equally_and_drops_one_sided(self):
        rows = [("a", 0, "yes", 1), ("a", 0, "no", 0)] * 8
        rows += [("b", 0, "yes", 0), ("b", 0, "no", 1)]
        rows += [("c", 0, "yes", 1)]
        x = pd.DataFrame(rows, columns=["date", "block", "state", "hit"])
        detail, daily = within_blocks(x)
        self.assertEqual(len(detail), 3)
        self.assertEqual(detail.both.sum(), 2)
        self.assertAlmostEqual(daily.delta.mean(), 0.)

    def test_empty_strata_are_unestimable(self):
        detail, daily = within_blocks(pd.DataFrame(columns=["date", "block", "state", "hit"]))
        self.assertEqual(len(detail), 0)
        self.assertEqual(len(daily), 0)


if __name__ == "__main__":
    unittest.main()
