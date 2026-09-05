from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

import pandas as pd


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "render_pandar_approved_master.py"
SPEC = importlib.util.spec_from_file_location("render_pandar_approved_master", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MASTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MASTER
SPEC.loader.exec_module(MASTER)


class PandarMasterTests(unittest.TestCase):
    def test_later_period_keeps_only_pandar_methods_and_call_boundary(self) -> None:
        rows = pd.DataFrame(
            [
                {"tradeDate": "2026-08-24", "ticker": "AAA", "scenario": "sell-first call grab"},
                {"tradeDate": "2026-08-24", "ticker": "BBB", "scenario": "buy-first put-tail inventory"},
                {"tradeDate": "2026-08-28", "ticker": "CCC", "scenario": "sell-first call grab"},
                {"tradeDate": "2026-08-28", "ticker": "DDD", "scenario": "buy-first call puke"},
            ]
        )

        actual = MASTER.filter_approved_rows(
            rows,
            source_dataset="test",
            later_period=True,
        )

        self.assertEqual(set(actual["ticker"]), {"BBB", "CCC"})
        self.assertEqual(set(actual["scenario"]), set(MASTER.PANDAR_METHODS))

    def test_legacy_sell_first_alias_is_canonicalized(self) -> None:
        rows = pd.DataFrame(
            [
                {"tradeDate": "2026-08-11", "ticker": "AAA", "scenario": "sell-first"},
                {"tradeDate": "2026-08-11", "ticker": "BBB", "scenario": "buy-first puke"},
            ]
        )

        actual = MASTER.filter_approved_rows(
            rows,
            source_dataset="test",
            legacy=True,
        )

        self.assertEqual(actual.iloc[0]["scenario"], "sell-first call grab")
        self.assertEqual(list(actual["ticker"]), ["AAA"])

    def test_coverage_marks_unpublished_end_date_unavailable(self) -> None:
        master = pd.DataFrame(
            columns=["tradeDate", "ticker", "scenario", "chain_confirmed"]
        )

        coverage = MASTER.build_daily_coverage(master)
        end = coverage.loc[coverage["tradeDate"].eq("2026-09-04")]

        self.assertEqual(set(end["signal_data_status"]), {"provider_unavailable"})
        self.assertEqual(int(end["surface_count"].sum()), 0)


if __name__ == "__main__":
    unittest.main()
