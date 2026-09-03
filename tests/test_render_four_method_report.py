from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

import pandas as pd


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "render_four_method_report.py"
SPEC = importlib.util.spec_from_file_location("render_four_method_report", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
REPORT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REPORT
SPEC.loader.exec_module(REPORT)


class ReportFormattingTests(unittest.TestCase):
    def test_put_contract_uses_complete_spread_not_leg_in_language(self) -> None:
        row = pd.Series(
            {
                "scenario": "buy-first put-tail inventory",
                "option_side": "put",
                "expiry": "2026-09-18",
                "leg1_strike": 130,
                "leg2_strike": 125,
                "entry_cash": 0.01,
            }
        )

        self.assertEqual(
            REPORT.contract_text(row),
            "BTO 09-18 130/125P complete spread at ≤$0.01",
        )

    def test_sell_contract_keeps_sell_first_order(self) -> None:
        row = pd.Series(
            {
                "scenario": "sell-first call grab",
                "option_side": "call",
                "expiry": "2026-09-04",
                "leg1_strike": 160,
                "leg2_strike": 157.5,
                "entry_cash": 0.23,
                "target_leg2_price": 0.13,
            }
        )

        self.assertEqual(
            REPORT.contract_text(row),
            "STO 09-04 160C at ≥$0.23; rest BTO 157.5C at $0.13",
        )


if __name__ == "__main__":
    unittest.main()
