"""hiro_watch/events.py — the event-day policy as data (stand down on FOMC only; tag the rest)."""
from __future__ import annotations

from pathlib import Path

from hiro_engine.calendar import CalendarLoader
from hiro_watch import events as E


def test_tag_covers_every_type():
    assert E.tag("2026-09-16") == "fomc"
    assert E.tag("2026-09-11") == "cpi"
    assert E.tag("2026-09-04") == "nfp"
    assert E.tag("2026-09-18") == "quarterly_opex"
    assert E.tag("2026-08-31") == "month_end_rebalance"
    assert E.tag("2026-09-09") == ""


def test_written_csv_makes_the_engine_stand_down_on_fomc_only(tmp_path):
    p = tmp_path / "cal.csv"
    E.write(p)
    cal = CalendarLoader(p)
    flagged = {d for d, _ in E.rows() if cal.is_event_day(d)}
    assert flagged == {d for d, r in E.rows() if r == "fomc"} == {d for d in E.FOMC if E.START.isoformat() <= d <= E.END.isoformat()}
    assert not cal.is_event_day("2026-09-04") and not cal.is_event_day("2026-08-31")


def test_repo_csv_is_current():
    assert E.CALENDAR_CSV.read_text().splitlines()[1:] == [f"{d},{r}" for d, r in E.rows()]
