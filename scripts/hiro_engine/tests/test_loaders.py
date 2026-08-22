"""Task 2 tests: loaders load a known day bar-for-bar; refusal lists dates; stale levels invalid."""
from __future__ import annotations

import pytest

from hiro_engine.calendar import CalendarLoader
from hiro_engine.feeds import FeedError, ReplayFeed, load_hiro_day, load_spx_day
from hiro_engine.levels import LevelsLoader


DAY = "2026-08-12"


def test_known_day_loads_bar_for_bar(config):
    feed = ReplayFeed(config, [DAY])
    ticks = list(feed.iter_day(DAY))
    spx = load_spx_day(config.path_of("spx_dir"), DAY)
    spx = spx[(spx["min"] >= 570) & (spx["min"] <= 960)]
    assert len(ticks) == len(spx)
    assert ticks[0].bar.min == 570
    # HIRO truncation is causal: last row of the frame == the bar's minute (or earlier)
    t = ticks[40]
    assert t.hiro is not None and t.hiro["min"].max() <= t.bar.min


def test_hiro_frame_matches_research_loader(config):
    """Engine loader == hiro_setup_dashboard.load_day for the shared columns."""
    import sys
    sys.path.insert(0, "scripts")
    from hiro_setup_dashboard import load_day as research_load_day
    ours = load_hiro_day(config.path_of("hiro_root"), DAY)
    theirs = research_load_day(DAY)   # merged with SPX; compare on shared minutes
    merged = theirs.merge(ours, on="min", suffixes=("_r", "_e"))
    for col in ("all_L", "all_Lc", "all_Lp", "nextExp_L"):
        assert (merged[f"{col}_r"] - merged[f"{col}_e"]).abs().max() < 1e-9


def test_missing_date_refused_and_listed(config):
    with pytest.raises(FeedError) as ei:
        ReplayFeed(config, ["2026-08-12", "2031-01-02"])
    assert "2031-01-02" in str(ei.value)


def test_stale_levels_invalid(config, tmp_path):
    loader = LevelsLoader(config.path_of("levels_csv"))
    lv = loader.load("2026-08-21")
    assert lv.valid and lv.vt == 7690 and lv.cw == 7900
    assert loader.load("2031-01-02").valid is False     # no row for that date
    bad = tmp_path / "levels.csv"
    bad.write_text("Date,sg_index,Net Delta,Call Wall,Put Wall,Vol Trigger,pivot,pivot_updated\n"
                   "2026-08-21,-0.6,1,7600,7500,7690,,\n")   # CW - VT < 0
    assert LevelsLoader(bad).load("2026-08-21").valid is False


def test_calendar_rules(config, tmp_path):
    cal = CalendarLoader(config.path_of("calendar_csv"))
    assert cal.check("2026-08-07").reason == "nfp"            # first Friday Aug 2026
    assert cal.check("2026-09-18").reason == "quarterly_opex" # 3rd Friday Sep
    assert cal.check("2026-08-31").reason == "month_end_rebalance"
    assert cal.is_event_day("2026-08-12") is False            # manual CSV is empty
    manual = tmp_path / "cal.csv"
    manual.write_text("date,reason\n2026-08-12,cpi\n")
    assert CalendarLoader(manual).check("2026-08-12").reason == "cpi"
