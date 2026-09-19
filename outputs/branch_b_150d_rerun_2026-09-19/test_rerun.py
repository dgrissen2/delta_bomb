"""Adversarial tests for regime admission and first-touch accounting."""
import unittest

import numpy as np
import pandas as pd

from rerun_core import distinct_entries, score, thin_entries, vt_flags


class CausalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = pd.DataFrame({'min':np.arange(570,960),'open':6010.0,
                                 'high':6011.0,'low':6009.0,'close':6010.0}).set_index('min')

    def test_future_vt_breach_does_not_exclude_entry(self) -> None:
        self.raw.loc[700,'low'] = 5990.0
        self.assertTrue(vt_flags(self.raw,600,6000)['always_above'])

    def test_entry_bar_later_low_does_not_exclude_entry(self) -> None:
        self.raw.loc[600,'low'] = 5990.0
        self.assertTrue(vt_flags(self.raw,600,6000)['always_above'])

    def test_earlier_breach_locks_out_reclaim(self) -> None:
        self.raw.loc[580,'low'] = 5990.0
        flags = vt_flags(self.raw,600,6000)
        self.assertTrue(flags['entry_above'])
        self.assertFalse(flags['always_above'])

    def test_equality_is_not_above(self) -> None:
        self.raw.loc[590,'low'] = 6000.0
        self.assertFalse(vt_flags(self.raw,600,6000)['always_above'])

    def test_missing_history_is_not_continuously_above(self) -> None:
        with self.assertRaises(ValueError):
            vt_flags(self.raw.drop(index=580),600,6000)

    def test_invalid_vt_rejected(self) -> None:
        for vt in [True,np.nan,np.inf,0]:
            with self.subTest(vt=vt), self.assertRaises(ValueError):
                vt_flags(self.raw,600,vt)

    def test_target_then_reversal_remains_win(self) -> None:
        self.raw.loc[602,'high'] = 6015
        self.raw.loc[610,'low'] = 5995
        self.assertEqual(score(self.raw,600)['outcome'],'target_first')

    def test_same_minute_order_is_ambiguous(self) -> None:
        self.raw.loc[602,['high','low']] = [6015,5995]
        self.assertEqual(score(self.raw,600)['outcome'],'ambiguous')

    def test_missing_outcome_minute_raises(self) -> None:
        with self.assertRaises(ValueError):
            score(self.raw.drop(index=620),600)

    def test_neither_is_retained(self) -> None:
        self.assertEqual(score(self.raw,600)['outcome'],'neither')


class AccountingTests(unittest.TestCase):
    def test_overlapping_setups_are_one_price_opportunity(self) -> None:
        events = pd.DataFrame({'date':['2026-01-06']*4,'variant':['b07']*3+['b09'],
                               'known_min':[600,600,605,600],'event_id':['a','b','c','d']})
        result = distinct_entries(events)
        self.assertEqual(len(result),3)
        self.assertEqual(len(events),4)

    def test_cooldown_uses_last_accepted_entry_and_resets_by_day(self) -> None:
        events = pd.DataFrame({'date':['2026-01-06']*4+['2026-01-07'],
            'variant':['b09']*5,'known_min':[600,630,660,719,600],
            'event_id':['a','b','c','d','e']})
        result = thin_entries(events,60)
        self.assertEqual(result.event_id.tolist(),['a','c','e'])


if __name__ == '__main__':
    unittest.main()
