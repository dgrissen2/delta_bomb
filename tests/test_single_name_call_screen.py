from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "single_name_call_screen.py"
SPEC = importlib.util.spec_from_file_location("single_name_call_screen", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SCREEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SCREEN
SPEC.loader.exec_module(SCREEN)


class PercentileTests(unittest.TestCase):
    def test_percentile_uses_only_prior_observations(self) -> None:
        history = np.array([1.0, 2.0, 3.0, np.nan])
        self.assertAlmostEqual(
            SCREEN.prior_percentile(history, 3.0, min_observations=3), 200 / 3
        )

    def test_percentile_requires_minimum_history(self) -> None:
        history = np.array([1.0, 2.0, np.nan])
        self.assertTrue(
            np.isnan(SCREEN.prior_percentile(history, 3.0, min_observations=3))
        )


class SignalTests(unittest.TestCase):
    def test_canonical_strategy_names_are_stable(self) -> None:
        self.assertEqual(SCREEN.BUY_FIRST_CALL_PUKE, "buy-first call puke")
        self.assertEqual(SCREEN.BUY_FIRST_CALL_STANDARD, "buy-first call standard")
        self.assertEqual(SCREEN.SELL_FIRST_CALL_GRAB, "sell-first call grab")
        self.assertEqual(
            SCREEN.BUY_FIRST_PUT_TAIL_INVENTORY,
            "buy-first put-tail inventory",
        )

    def test_read_ticker_universe_normalizes_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            universe_path = Path(temp_dir) / "tickers.csv"
            universe_path.write_text("Ticker\nnvda\nAAPL\nNVDA\n\n")

            self.assertEqual(
                SCREEN.read_ticker_universe(universe_path),
                frozenset({"AAPL", "NVDA"}),
            )

    def test_buy_first_tiers_are_nested_and_use_vol_points(self) -> None:
        self.assertEqual(SCREEN.buy_first_tier(20, 95, 5, 0.5, True), "best")
        self.assertEqual(SCREEN.buy_first_tier(30, 85, 20, 1.5, False), "better")
        self.assertEqual(SCREEN.buy_first_tier(45, 65, 35, 2.5, False), "good")
        self.assertEqual(SCREEN.buy_first_tier(45, 65, 35, 3.5, False), "")

    def test_sell_first_archetypes_are_distinct(self) -> None:
        self.assertEqual(SCREEN.sell_first_archetype(90, 75, 5, 60, 50, 2.0), "grab")
        self.assertEqual(
            SCREEN.sell_first_archetype(90, 75, 80, 90, 85, -2.0),
            "post-shock smile",
        )
        self.assertEqual(SCREEN.sell_first_archetype(90, 75, 40, 60, 50, -1.0), "other")
        self.assertEqual(SCREEN.sell_first_archetype(80, 75, 5, 60, 50, 2.0), "")

    def test_sell_first_actionability_enforces_grab_regime(self) -> None:
        self.assertTrue(SCREEN.sell_first_is_actionable("grab", -4.0, 50.0, False))
        self.assertFalse(SCREEN.sell_first_is_actionable("grab", -6.0, 50.0, False))
        self.assertFalse(SCREEN.sell_first_is_actionable("grab", -4.0, 80.0, False))
        self.assertTrue(
            SCREEN.sell_first_is_actionable("post-shock smile", -20.0, 90.0, False)
        )
        self.assertFalse(
            SCREEN.sell_first_is_actionable("post-shock smile", -2.0, 50.0, True)
        )

    def test_put_tail_inventory_requires_cheap_put_surface(self) -> None:
        self.assertTrue(SCREEN.put_tail_inventory_is_actionable(25, 40, 20))
        self.assertFalse(SCREEN.put_tail_inventory_is_actionable(36, 40, 20))
        self.assertFalse(SCREEN.put_tail_inventory_is_actionable(25, 51, 20))
        self.assertFalse(SCREEN.put_tail_inventory_is_actionable(25, 40, 26))

    def test_scenario_expansion_preserves_overlapping_methods_and_windows(self) -> None:
        signals = pd.DataFrame(
            [
                {
                    "tradeDate": "2026-08-24",
                    "ticker": "AAA",
                    "liquid_final": True,
                    "buy_first_puke": True,
                    "buy_first_standard": False,
                    "sell_first_actionable": False,
                    "buy_first_put_tail_inventory": True,
                    "buy_score": 10.0,
                    "sell_score": 20.0,
                    "put_inventory_score": 30.0,
                },
                {
                    "tradeDate": "2026-08-28",
                    "ticker": "BBB",
                    "liquid_final": True,
                    "buy_first_puke": True,
                    "buy_first_standard": False,
                    "sell_first_actionable": False,
                    "buy_first_put_tail_inventory": True,
                    "buy_score": 11.0,
                    "sell_score": 21.0,
                    "put_inventory_score": 31.0,
                },
            ]
        )

        selected = SCREEN.expand_scenario_candidates(
            signals,
            call_start="2026-08-28",
            put_start="2026-08-24",
        )

        self.assertEqual(
            list(
                selected[["tradeDate", "ticker", "scenario"]].itertuples(
                    index=False,
                    name=None,
                )
            ),
            [
                ("2026-08-24", "AAA", "buy-first put-tail inventory"),
                ("2026-08-28", "BBB", "buy-first call puke"),
                ("2026-08-28", "BBB", "buy-first put-tail inventory"),
            ],
        )

    def test_orats_synthetic_aliases_are_not_single_stocks(self) -> None:
        self.assertTrue(SCREEN.is_single_stock_ticker("NVDA"))
        self.assertFalse(SCREEN.is_single_stock_ticker("XLY_C"))
        self.assertFalse(SCREEN.is_single_stock_ticker("SPX"))
        self.assertFalse(SCREEN.is_single_stock_ticker("KRE"))
        self.assertFalse(SCREEN.is_single_stock_ticker("URA"))
        self.assertFalse(SCREEN.is_single_stock_ticker("XHB"))

    def test_single_stock_metadata_rejects_sector_etfs(self) -> None:
        self.assertTrue(
            SCREEN.has_single_stock_metadata("Semiconductors", "XLK", "NVDA")
        )
        self.assertFalse(SCREEN.has_single_stock_metadata("N/A", "XLF", "XLF"))
        self.assertFalse(
            SCREEN.has_single_stock_metadata(
                "Natural Resource Equities",
                "XLB",
                "XLB",
            )
        )

    def test_trading_calendar_refreshes_when_cached_history_is_stale(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.calls = []

            def get(self, endpoint, params):
                self.calls.append((endpoint, params))
                return [
                    {"ticker": "SPY", "tradeDate": "2026-08-26", "clsPx": 1},
                    {"ticker": "SPY", "tradeDate": "2026-08-27", "clsPx": 1},
                ]

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            path = cache_dir / "hist_dailies" / "SPY_full_history.json.gz"
            SCREEN.write_gzip_json(
                path,
                [{"ticker": "SPY", "tradeDate": "2026-08-21", "clsPx": 1}],
            )
            client = FakeClient()

            dates = SCREEN.get_trading_dates(client, cache_dir, "2026-08-27")

            self.assertEqual(dates, ["2026-08-26", "2026-08-27"])
            self.assertEqual(len(client.calls), 1)
            self.assertEqual(
                SCREEN.read_gzip_json(path)[-1]["tradeDate"], "2026-08-27"
            )

    def test_full_history_batch_cache_loads_only_requested_dates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            SCREEN.write_gzip_json(
                SCREEN.batch_history_cache_path(
                    cache_dir,
                    "hist/summaries",
                    ["AAPL", "NVDA"],
                ),
                [
                    {"ticker": "AAPL", "tradeDate": "2026-08-20", "iv30d": 0.3},
                    {"ticker": "AAPL", "tradeDate": "2026-08-21", "iv30d": 0.4},
                    {"ticker": "NVDA", "tradeDate": "2026-08-21", "iv30d": 0.5},
                ],
            )

            loaded = SCREEN.load_cached_history_batches(
                cache_dir,
                "hist/summaries",
                ["2026-08-21"],
            )

            self.assertEqual(set(loaded["ticker"]), {"AAPL", "NVDA"})
            self.assertEqual(set(loaded["tradeDate"]), {"2026-08-21"})

    def test_full_history_batch_fetch_omits_trade_date(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.calls = []

            def get(self, endpoint, params):
                self.calls.append((endpoint, params))
                return [{"ticker": "NVDA", "tradeDate": "2026-08-27"}]

        with tempfile.TemporaryDirectory() as temp_dir:
            client = FakeClient()
            _, fetched, rows = SCREEN.fetch_batch_history_to_cache(
                client,
                Path(temp_dir),
                "hist/summaries",
                ["AAPL", "NVDA"],
                SCREEN.SUMMARY_FIELDS,
            )

            self.assertTrue(fetched)
            self.assertEqual(rows, 1)
            self.assertEqual(client.calls[0][0], "hist/summaries")
            self.assertEqual(client.calls[0][1]["ticker"], "AAPL,NVDA")
            self.assertNotIn("tradeDate", client.calls[0][1])


class ContractSelectionTests(unittest.TestCase):
    def test_sell_first_selects_four_delta_weekly_with_tight_quote(self) -> None:
        chain = pd.DataFrame(
            [
                self._row(100, 0.50, 5.0, 5.1, 0.40),
                self._row(105, 0.10, 0.8, 0.9, 0.45),
                self._row(110, 0.04, 0.25, 0.30, 0.50),
            ]
        )
        selected = SCREEN.select_sell_contract(chain, set())
        self.assertEqual(selected["leg1_strike"], 110)
        self.assertEqual(selected["leg2_strike"], 105)
        self.assertTrue(selected["chain_confirmed"])

    def test_standard_buy_selects_fifteen_delta_monthly(self) -> None:
        chain = pd.DataFrame(
            [
                self._row(100, 0.15, 1.0, 1.1, 0.40, dte=45),
                self._row(105, 0.10, 0.75, 0.80, 0.42, dte=45),
            ]
        )
        selected = SCREEN.select_standard_buy_contract(chain, set())
        self.assertEqual(selected["leg1_strike"], 100)
        self.assertEqual(selected["leg2_strike"], 105)
        self.assertTrue(selected["chain_confirmed"])

    def test_puke_buy_selects_cheap_five_wide_spread(self) -> None:
        chain = pd.DataFrame(
            [
                self._row(125, 0.08, 0.25, 0.30, 0.55, dte=45, spot=100),
                self._row(130, 0.05, 0.20, 0.25, 0.57, dte=45, spot=100),
            ]
        )
        selected = SCREEN.select_puke_buy_spread(chain, set())
        self.assertEqual(selected["leg1_strike"], 125)
        self.assertEqual(selected["leg2_strike"], 130)
        self.assertAlmostEqual(selected["entry_cash"], 0.10)
        self.assertTrue(selected["chain_confirmed"])

    def test_put_tail_inventory_selects_ten_cent_monthly_spread(self) -> None:
        chain = pd.DataFrame(
            [
                self._row(
                    75,
                    0.95,
                    0.01,
                    0.02,
                    0.40,
                    dte=25,
                    expiry="2026-09-18",
                    put_bid=0.11,
                    put_ask=0.12,
                ),
                self._row(
                    70,
                    0.97,
                    0.01,
                    0.02,
                    0.42,
                    dte=25,
                    expiry="2026-09-18",
                    put_bid=0.03,
                    put_ask=0.04,
                ),
            ]
        )

        selected = SCREEN.select_put_tail_inventory_spread(chain, set())

        self.assertEqual(selected["option_side"], "put")
        self.assertEqual(selected["leg1_strike"], 75)
        self.assertEqual(selected["leg2_strike"], 70)
        self.assertAlmostEqual(selected["entry_cash"], 0.09)
        self.assertTrue(selected["chain_confirmed"])

    @staticmethod
    def _row(
        strike: float,
        delta: float,
        bid: float,
        ask: float,
        iv: float,
        *,
        dte: int = 10,
        spot: float = 100,
        expiry: str | None = None,
        put_bid: float = 0.01,
        put_ask: float = 0.02,
    ) -> dict[str, float | int | str]:
        return {
            "ticker": "TEST",
            "tradeDate": "2026-08-12",
            "expirDate": expiry or ("2026-08-21" if dte == 10 else "2026-09-25"),
            "dte": dte,
            "strike": strike,
            "stockPrice": spot,
            "delta": delta,
            "callBidPrice": bid,
            "callAskPrice": ask,
            "callMidIv": iv,
            "callOpenInterest": 100,
            "callVolume": 20,
            "putBidPrice": put_bid,
            "putAskPrice": put_ask,
            "putMidIv": iv,
            "putOpenInterest": 100,
            "putVolume": 20,
        }


if __name__ == "__main__":
    unittest.main()
