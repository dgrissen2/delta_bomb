from __future__ import annotations

from datetime import date, datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

import pandas as pd


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "hiro_single_name_backfill.py"
SPEC = importlib.util.spec_from_file_location("hiro_single_name_backfill", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
BACKFILL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BACKFILL
SPEC.loader.exec_module(BACKFILL)


class TickerWindowTests(unittest.TestCase):
    def test_incremental_candidates_union_prior_and_current_inventory(self) -> None:
        current = pd.DataFrame(
            [
                {"tradeDate": "2026-08-24", "ticker": "AAA"},
                {"tradeDate": "2026-09-01", "ticker": "BBB"},
            ]
        )
        prior = pd.DataFrame([{"ticker": "AAA"}, {"ticker": "OLD"}])

        merged = BACKFILL.build_incremental_candidates(
            current,
            prior,
            prior_end_date=date(2026, 8, 28),
        )

        self.assertEqual(
            list(merged.itertuples(index=False, name=None)),
            [
                ("AAA", "2026-08-28", "prior inventory refresh"),
                ("BBB", "2026-09-01", "new surface qualifier"),
                ("OLD", "2026-08-28", "prior inventory refresh"),
            ],
        )

    def test_ticker_windows_start_after_each_tickers_first_signal(self) -> None:
        candidates = pd.DataFrame(
            [
                {"tradeDate": "2026-08-11", "ticker": "AAA"},
                {"tradeDate": "2026-08-14", "ticker": "AAA"},
                {"tradeDate": "2026-08-21", "ticker": "BBB"},
            ]
        )

        windows = BACKFILL.build_ticker_windows(candidates, end_date=date(2026, 8, 28))

        self.assertEqual(
            windows,
            [
                BACKFILL.TickerWindow("AAA", date(2026, 8, 12), date(2026, 8, 28)),
                BACKFILL.TickerWindow("BBB", date(2026, 8, 22), date(2026, 8, 28)),
            ],
        )

    def test_followup_partition_leaves_end_date_signals_pending(self) -> None:
        candidates = pd.DataFrame(
            [
                {"ticker": "READY", "tradeDate": "2026-09-01"},
                {"ticker": "PENDING", "tradeDate": "2026-09-02"},
            ]
        )

        eligible, pending = BACKFILL.partition_followup_candidates(
            candidates,
            end_date=date(2026, 9, 2),
        )

        self.assertEqual(eligible["ticker"].tolist(), ["READY"])
        self.assertEqual(pending["ticker"].tolist(), ["PENDING"])

    def test_ticker_windows_reject_signal_after_end_date(self) -> None:
        candidates = pd.DataFrame([{"tradeDate": "2026-08-29", "ticker": "AAA"}])

        with self.assertRaisesRegex(ValueError, "after the requested end date"):
            BACKFILL.build_ticker_windows(candidates, end_date=date(2026, 8, 28))


class PayloadSplitTests(unittest.TestCase):
    def test_split_payload_uses_new_york_session_dates_and_preserves_groups(self) -> None:
        aug_27_late = int(
            datetime(2026, 8, 28, 3, 59, tzinfo=timezone.utc).timestamp() * 1_000
        )
        aug_28_open = int(
            datetime(2026, 8, 28, 13, 30, tzinfo=timezone.utc).timestamp() * 1_000
        )
        payload = {
            "AAA": {
                "all": [
                    {"utc_time": aug_27_late, "option_type": "C", "mid_signal": 1},
                    {"utc_time": aug_28_open, "option_type": "P", "mid_signal": -2},
                ],
                "nextExp": [
                    {"utc_time": aug_28_open, "option_type": "C", "mid_signal": 3}
                ],
                "retail": [],
            }
        }

        split = BACKFILL.split_payload_by_session(payload, ticker="AAA")

        self.assertEqual(sorted(split), [date(2026, 8, 27), date(2026, 8, 28)])
        self.assertEqual(len(split[date(2026, 8, 27)]["AAA"]["all"]), 1)
        self.assertEqual(len(split[date(2026, 8, 28)]["AAA"]["all"]), 1)
        self.assertEqual(len(split[date(2026, 8, 28)]["AAA"]["nextExp"]), 1)

    def test_requested_sessions_exclude_weekends(self) -> None:
        sessions = BACKFILL.requested_sessions(
            date(2026, 8, 22),
            date(2026, 8, 28),
        )

        self.assertEqual(
            sessions,
            [
                date(2026, 8, 24),
                date(2026, 8, 25),
                date(2026, 8, 26),
                date(2026, 8, 27),
                date(2026, 8, 28),
            ],
        )


if __name__ == "__main__":
    unittest.main()
