"""Targeted safety tests for the frozen 150-day extension."""

from datetime import date
from pathlib import Path
import tempfile
import unittest

import pandas as pd
import numpy as np

from collect import load_levels, exclude_prior_days, request_key, select_expiries, sampler
from iv_rules import classify, slopes, check_guard_boundaries
from recalculate import legacy


class PriceScoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bars = pd.DataFrame({'min': np.arange(600,660), 'open': 6000.0,
                                  'high': 6001.0, 'low': 5999.0, 'close': 6000.0})

    def test_later_reversal_does_not_change_first_target(self) -> None:
        self.bars.loc[3,'high'] = 6005.0
        self.bars.loc[20,'low'] = 5985.0
        self.assertEqual(legacy.score_path(self.bars,600,6000)['outcome'], 'target_first')

    def test_same_minute_both_barriers_is_ambiguous(self) -> None:
        self.bars.loc[3,['high','low']] = [6005.0,5985.0]
        self.assertEqual(legacy.score_path(self.bars,600,6000)['outcome'], 'ambiguous')

    def test_missing_outcome_minute_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, 'Missing'):
            legacy.score_path(self.bars.drop(index=20),600,6000)


class FrozenRuleTests(unittest.TestCase):
    def test_unknowns_not_silently_dropped(self) -> None:
        self.assertEqual(classify(6, 5), 'yes')
        self.assertEqual(classify(5, 1), 'unknown')
        self.assertEqual(classify(4, 1), 'no')
        with self.assertRaises(ValueError):
            classify(6, 6)

    def test_missing_minute_invalidates_both_slopes(self) -> None:
        window = np.arange(30, dtype=float)
        self.assertEqual(slopes(window), (1.0, 1.0, 0.0))
        window[4] = np.nan
        self.assertTrue(all(np.isnan(value) for value in slopes(window)))
        with self.assertRaises(ValueError):
            slopes(np.arange(29))

    def test_original_guard_boundaries(self) -> None:
        self.assertEqual(check_guard_boundaries(), 10)


class SamplingTests(unittest.TestCase):
    def test_frozen_draw_reuses_seed_and_rejects_changed_population(self) -> None:
        days = pd.date_range('2025-01-01', periods=110).strftime('%Y-%m-%d').tolist()
        ledger = pd.DataFrame({'date':days, 'eligible':True, 'exclusion_reasons':''})
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            first = sampler.freeze_sample(ledger, {}, {}, out, count=100)
            second = sampler.freeze_sample(ledger, {}, {}, out, count=100)
            self.assertEqual(len(first),100)
            self.assertTrue(first.date.is_unique)
            pd.testing.assert_frame_equal(first,second)
            ledger.loc[0,'eligible'] = False
            ledger.loc[0,'exclusion_reasons'] = 'incomplete_spx'
            with self.assertRaisesRegex(ValueError, 'refuse to reroll'):
                sampler.freeze_sample(ledger, {}, {}, out, count=100)

    def test_date_bounds_and_duplicate_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'vt.csv'
            path.write_text('Date,Vol Trigger\n2024-12-31,1\n2025-01-02,5900\n'
                            '2026-09-18,7000\n2026-09-21,7100\n')
            rows = load_levels(path)
            self.assertEqual([r['date'] for r in rows], ['2025-01-02', '2026-09-18'])
            path.write_text('Date,Vol Trigger\n2025-01-02,5900\n2025-01-02,5900\n')
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                load_levels(path)

    def test_prior_days_never_reenter(self) -> None:
        frame = pd.DataFrame({'date': ['2025-01-02','2026-01-06','2026-01-07'],
                              'eligible': [True,True,False],
                              'exclusion_reasons': ['', '', 'missing_spx']})
        result = exclude_prior_days(frame, {'2026-01-06'})
        self.assertEqual(result.eligible.tolist(), [True,False,False])
        self.assertEqual(result.exclusion_reasons.iloc[1], 'original_fifty_day')
        self.assertTrue(frame.eligible.iloc[1])

    def test_request_identity_preserves_parameters(self) -> None:
        self.assertEqual(request_key('test', {'date':date(2025,1,2)}),
                         request_key('test', {'date':'2025-01-02'}))
        self.assertNotEqual(request_key('test', {'interval':'1m'}),
                            request_key('test', {'interval':'5m'}))

    def test_expiry_bracket_never_extrapolates(self) -> None:
        day = date(2025,1,2)
        self.assertEqual(select_expiries(day, [date(2025,1,17)]), [])
        self.assertEqual(select_expiries(day, [date(2025,2,1)]), [date(2025,2,1)])
        self.assertEqual(select_expiries(day, [date(2025,1,3),date(2025,1,17),
                                              date(2025,2,21),date(2025,4,1)]),
                         [date(2025,1,17),date(2025,2,21)])


if __name__ == '__main__':
    unittest.main()
