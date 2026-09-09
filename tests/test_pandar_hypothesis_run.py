"""Provider timestamps must merge causally without inventing observations."""

import numpy as np
import pandas as pd
import pytest

from scripts.pandar_hypothesis_run import (
    earnings_statuses, merge_leg, replay_population, summarize_replay, timestamp_index,
)


def test_theta_naive_clock_is_eastern_not_utc():
    index = timestamp_index(pd.Series(["2026-06-12T10:01:00"]))
    assert str(index[0]) == "2026-06-12 10:01:00-04:00"
    assert index[0].tz_convert("UTC").hour == 14


def test_exact_merge_does_not_forward_fill_greeks():
    q = pd.DataFrame({"timestamp": ["2026-06-12 10:01", "2026-06-12 10:02"],
                      "bid": [.20, .22], "ask": [.25, .27]})
    g = pd.DataFrame({"timestamp": ["2026-06-12 10:01"], "delta": [.08],
                      "underlying_timestamp": ["2026-06-12 10:00:59.990"],
                      "underlying_price": [100.]})
    merged = merge_leg(q, g, "far")
    assert merged.iloc[0].far_delta == .08
    assert pd.isna(merged.iloc[1].far_delta)
    assert "far_quote_timestamp" not in merged


def test_quote_prices_win_and_greek_prices_cannot_fill_missing_quotes():
    quotes = pd.DataFrame({"timestamp": ["2026-06-12 10:01"], "bid": [.2], "ask": [.3]})
    greeks = pd.DataFrame({"timestamp": ["2026-06-12 10:01", "2026-06-12 10:02"],
                           "bid": [9., 8.], "ask": [10., 9.], "delta": [.08, .07]})
    merged = merge_leg(quotes, greeks, "near", quote_source_path="quotes.parquet",
                       greek_source_path="greeks.parquet")
    assert merged.iloc[0].near_bid == .2 and merged.iloc[0].near_greek_bid == 9.
    assert pd.isna(merged.iloc[1].near_bid)
    assert merged.iloc[0].near_quote_source_path == "quotes.parquet"
    assert merged.iloc[0].near_greek_timestamp == merged.index[0]
    assert "near_quote_timestamp" not in merged
    with pytest.raises(ValueError, match="duplicate"):
        merge_leg(pd.concat([quotes, quotes]), greeks, "near")


def test_earnings_window_is_inclusive_and_missing_coverage_is_unknown():
    events = pd.DataFrame({"ticker": ["A", "A"], "earnDate": ["2026-07-12", "2026-09-01"]})
    coverage = pd.DataFrame({"ticker": ["A"], "earnings_status": ["ok"],
                             "earnings_coverage_start": ["2020-01-01"],
                             "earnings_coverage_end": ["2026-09-04"]})
    result = earnings_statuses("A", ["2026-06-11", "2026-06-12"], events, coverage)
    assert result == {"2026-06-11": "clear", "2026-06-12": "event_in_next_30_days"}
    assert earnings_statuses("B", ["2026-06-11"], events, coverage)["2026-06-11"] == "unknown"
    assert earnings_statuses("A", ["2026-08-10"], events, coverage)["2026-08-10"] == "unknown"


def cases():
    days = ["2026-06-12", "2026-06-15", "2026-06-16", "2026-06-17", "2026-06-18"]
    base = {"tradeDate": "2026-06-11", "entry_date": days[0], "expiry": "2026-06-26",
            "far_strike": 120., "near_strike": 115.,
            **{f"holding_session_{i+1}": day for i, day in enumerate(days)}}
    return pd.DataFrame([{**base, "ticker": "NOEXP", "selection_status": "no_expiry_in_dte_band"},
                         {**base, "ticker": "MISSING", "selection_status": "missing_signal_chain"}])


def test_no_selection_and_missing_cases_retain_40_rows_and_full_denominator():
    table = replay_population(cases(), [], pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                               variant="original")
    assert len(table) == 80
    assert table.groupby("ticker").size().to_dict() == {"MISSING": 40, "NOEXP": 40}
    assert table.loc[table.ticker.eq("NOEXP"), "pnl_net"].eq(0).all()
    assert table.loc[table.ticker.eq("MISSING"), "pnl_net"].isna().all()
    assert table.exit_at.str.contains("15:50:00").all()
    summary = summarize_replay(table)
    group = summary["policy_groups"][0]
    assert group["population_cases"] == 2 and group["priced_cases"] == 1
    assert group["censored_cases"] == 1 and group["mean_pnl_priced"] == 0
    assert group["comparisons"]["immediate_spread"]["paired_cases"] == 1
    assert summary["minimum_distinct_dates_required"] == 20
    assert summary["statistical_support"] == "inconclusive_fewer_than_20_dates"


def test_summary_rejects_duplicate_episode_weights_and_pairs_on_case_keys():
    table = replay_population(cases(), [], pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                               variant="original")
    with pytest.raises(ValueError, match="duplicate"):
        summarize_replay(pd.concat([table, table.iloc[:1]]))
    missing = table.ticker.eq("MISSING")
    table.loc[missing, "pnl_net"] = 5.
    table.loc[missing & table.entry_policy.eq("hiro"), "pnl_net"] = np.nan
    summary = summarize_replay(table)
    assert all(group["paired_cases"] == 1 for group in summary["entry_policy_comparisons"])


def test_variant_bounds_and_case_calendar_reach_replay_unchanged(monkeypatch):
    from scripts import pandar_hypothesis_run as adapter
    selected = cases().iloc[:1].copy()
    selected["ticker"], selected["selection_status"] = "A", "selected"
    captured = []

    def fake_replay(case, minutes, hiro):
        captured.append(case)
        return adapter.unavailable_case_rows(selected.iloc[0].to_dict(), "delta_5_15_otm5",
                                             "test_placeholder", known_no_entry=False)

    monkeypatch.setattr(adapter, "replay_case", fake_replay)
    monkeypatch.setattr(adapter, "load_case_minutes", lambda *args, **kwargs:
                        (pd.DataFrame(index=pd.DatetimeIndex([], tz="America/New_York")), []))
    table = adapter.replay_population(selected, [], pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                                      variant="delta_5_15_otm5")
    assert len(table) == 40
    assert (captured[0].far_delta_min, captured[0].far_delta_max, captured[0].far_otm_min_pct) == (.05, .15, 5.)
    assert captured[0].exchange_sessions[-1] == "2026-06-18"
    assert captured[0].multiplier_verified is False


def test_event_overlay_is_explicit_and_preserves_actual_source_time(monkeypatch):
    from scripts import pandar_hypothesis_run as adapter
    selected = cases().iloc[:1].copy()
    selected["ticker"], selected["selection_status"] = "A", "selected"
    stamp = pd.Timestamp("2026-06-12 10:01", tz="America/New_York")
    minute = pd.DataFrame({"far_bid": [.2]}, index=pd.DatetimeIndex([stamp]))
    captured = []

    def overlay(row, frame):
        assert row["ticker"] == "A"
        frame = frame.copy()
        frame["far_quote_timestamp"] = stamp - pd.Timedelta(seconds=2)
        return frame

    def fake_replay(case, frame, hiro):
        captured.append((case, frame))
        return adapter.unavailable_case_rows(selected.iloc[0].to_dict(), "delta10_otm5",
                                             "test_placeholder", known_no_entry=False)

    monkeypatch.setattr(adapter, "replay_case", fake_replay)
    monkeypatch.setattr(adapter, "load_case_minutes", lambda *args: (minute, []))
    adapter.replay_population(selected, [], pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                               variant="delta10_otm5", require_event_age=True,
                               minute_transform=overlay)
    assert captured[0][0].require_event_age is True
    assert captured[0][1].iloc[0].far_quote_timestamp == stamp - pd.Timedelta(seconds=2)
    assert "far_quote_timestamp" not in minute


def test_duplicate_manifest_and_wrong_source_contract_fail_closed(tmp_path):
    from scripts import pandar_hypothesis_run as adapter
    row = cases().iloc[0].to_dict()
    record = dict(ticker=row["ticker"], signal_date=row["tradeDate"], leg="far", kind="quote",
                  expiry=row["expiry"], strike=row["far_strike"], status="ok")
    with pytest.raises(ValueError, match="duplicate manifest"):
        adapter.load_case_minutes(row, [record, record])
    path = tmp_path / "wrong_contract.parquet"
    pd.DataFrame({"timestamp": ["2026-06-12 10:01"], "symbol": ["OTHER"],
                  "expiration": [row["expiry"]], "strike": [row["far_strike"]],
                  "right": ["call"], "bid": [.2], "ask": [.3]}).to_parquet(path)
    record["path"] = str(path)
    with pytest.raises(ValueError, match="contract identity mismatch"):
        adapter.load_case_minutes(row, [record])
