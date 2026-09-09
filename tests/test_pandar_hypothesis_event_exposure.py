"""An intraminute loss counts; a post-conversion or nonfirm quote cannot count."""

import pandas as pd

from scripts.pandar_hypothesis_event_exposure import event_cover_marks


def test_only_firm_events_inside_actual_short_phase():
    frame = pd.DataFrame({"timestamp": pd.date_range("2026-06-12 10:00:30", periods=4, freq="30s",
                                                      tz="America/New_York"),
                          "bid": [.3, .4, .5, .5], "ask": [.4, 1., 9., 8.],
                          "ask_size": [1, 1, 1, 1], "bid_condition": [50]*4,
                          "ask_condition": [50, 50, 7, 50]})
    marks = event_cover_marks(frame, pd.Timestamp("2026-06-12 10:00", tz="America/New_York"),
                              pd.Timestamp("2026-06-12 10:01:30", tz="America/New_York"), .5, .01)
    assert len(marks) == 2
    assert abs(marks.min() + 53.3) < 1e-9
