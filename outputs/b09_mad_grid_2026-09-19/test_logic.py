"""Meaningful boundary, missingness, timing and execution-policy checks."""
import unittest

import numpy as np
import pandas as pd

from logic import classify, choose_endpoint, describe, thin


class RuleTests(unittest.TestCase):
    def test_threshold_is_strict_and_breadth_is_inclusive(self):
        score = np.array([[1, 1.1, 1.2, 2.0]])
        b2 = np.full_like(score, -1)
        state, yes, missing = classify(score, b2, 1, 3, False)
        self.assertEqual((state[0], yes[0], missing[0]), ('yes', 3, 0))
        self.assertEqual(classify(score, b2, 1, 4, False)[0][0], 'no')

    def test_sign_and_falling_are_different_questions(self):
        score = np.array([[2.0, -5.0, 3.0]])
        b2 = np.array([[0.1, -0.2, -0.3]])
        self.assertEqual(classify(score, b2, 1, 2, False)[0][0], 'yes')
        self.assertEqual(classify(score, b2, 1, 2, True)[0][0], 'no')

    def test_missing_sector_bounds(self):
        score = np.array([[2, 2, np.nan, 0], [2, 0, np.nan, 0]])
        b2 = np.full_like(score, -1)
        self.assertEqual(classify(score, b2, 1, 2, False)[0].tolist(), ['yes', 'unknown'])
        self.assertEqual(classify(score, b2, 1, 4, False)[0].tolist(), ['no', 'no'])

    def test_false_conjunct_resolves_missing_other_leg(self):
        score = np.array([[np.nan, 0, 2]])
        b2 = np.array([[0.1, np.nan, np.nan]])
        state, yes, missing = classify(score, b2, 1, 1, True)
        self.assertEqual((state[0], yes[0], missing[0]), ('unknown', 0, 1))

    def test_flat_slope_is_not_falling(self):
        self.assertEqual(classify(np.array([[2.]]), np.array([[0.]]), 1, 1, True)[0][0], 'no')

    def test_invalid_shapes_and_infinite_values_fail(self):
        with self.assertRaises(ValueError):
            classify(np.zeros((1, 2)), np.zeros((1, 3)), 1, 1, False)
        with self.assertRaises(ValueError):
            classify(np.array([[np.inf]]), np.array([[-1.]]), 1, 1, False)


class ExecutionTests(unittest.TestCase):
    def test_exact_endpoint_never_carries_or_looks_forward(self):
        events = pd.DataFrame({'date': ['2025-01-02'] * 3, 'known_min': [600, 601, 602]})
        scores = pd.DataFrame({'date': ['2025-01-02'] * 2, 'end_min': [599, 601],
                               'signed_score': [2., 4.]})
        result = choose_endpoint(events, scores)
        self.assertEqual(result.signed_score.iloc[0], 2.)
        self.assertTrue(np.isnan(result.signed_score.iloc[1]))
        self.assertEqual(result.signed_score.iloc[2], 4.)

    def test_duplicate_endpoints_fail(self):
        events = pd.DataFrame({'date': ['d'], 'known_min': [600]})
        scores = pd.DataFrame({'date': ['d', 'd'], 'end_min': [599, 599]})
        with self.assertRaises(ValueError):
            choose_endpoint(events, scores)

    def test_spacing_is_causal_and_resets_daily(self):
        frame = pd.DataFrame({'date': ['a'] * 4 + ['b'],
                              'known_min': [600, 610, 659, 660, 600]})
        self.assertEqual(thin(frame, 'spaced60').index.tolist(), [0, 3, 4])
        self.assertEqual(thin(frame, 'first').index.tolist(), [0, 4])
        self.assertEqual(thin(frame.iloc[1:], 'spaced60').index.tolist(), [1, 4])

    def test_all_outcomes_stay_in_denominator(self):
        frame = pd.DataFrame({'date': ['a'] * 4, 'outcome':
                              ['target_first', 'adverse_first', 'neither', 'ambiguous']})
        result = describe(frame)
        self.assertEqual((result['n'], result['targets'], result['rate']), (4, 1, 25.))
        self.assertEqual(result['days'], 1)


if __name__ == '__main__':
    unittest.main()
