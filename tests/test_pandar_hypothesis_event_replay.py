"""Prove causal event alignment and missing-session handling independently of profits."""

import pandas as pd

from scripts.pandar_hypothesis_event_replay import overlay_events


def test_last_event_is_causal_and_no_cross_session_carry():
    index = pd.DatetimeIndex(["2026-06-12 10:01", "2026-06-12 10:02", "2026-06-15 10:01"],
                             tz="America/New_York")
    minutes = pd.DataFrame({"far_bid": [8., 8., 8.], "far_delta": [.1, None, .2]}, index=index)
    frame = pd.DataFrame({"timestamp": ["2026-06-12 10:00:56", "2026-06-12 10:01:00.001"],
                           "bid": [.2, .3], "ask": [.25, .35]})
    frame.timestamp = pd.to_datetime(frame.timestamp, format="mixed")
    records = [{"leg": "far", "session": "2026-06-12", "status": "ok", "path": "a"},
               {"leg": "far", "session": "2026-06-15", "status": "error"}]
    got = overlay_events(minutes, records, frames={"a": frame})
    assert got.iloc[0].far_bid == .2
    assert got.iloc[1].far_bid == .3
    assert pd.isna(got.iloc[2].far_bid)
    assert (index[0] - got.iloc[0].far_quote_timestamp).total_seconds() == 4
    assert pd.isna(got.iloc[1].far_delta)
    assert got.far_interval_bid.eq(8).all()
    assert got.iloc[2].far_event_history_status == "error"
    assert got.near_quote_timestamp.isna().all()
