"""CalendarLoader (R2.4): CPI, FOMC decision day, NFP, quarterly opex Friday,
month-end rebalance day.

Computed rules: NFP = first Friday of the month; quarterly opex = third Friday of
Mar/Jun/Sep/Dec; month-end rebalance = last weekday of the month. CPI and FOMC
release dates are irregular => maintained in the checked-in CSV
(docs/hiro_engine/event_calendar.csv: date,reason). The morning ops script warns
when the current month has no CPI/FOMC entries.
"""
from __future__ import annotations

import calendar as _cal
import csv
from datetime import date as _date
from pathlib import Path

from .models import CalendarDay


def _first_friday(y: int, m: int) -> _date:
    for d in range(1, 8):
        if _date(y, m, d).weekday() == 4:
            return _date(y, m, d)
    raise AssertionError


def _third_friday(y: int, m: int) -> _date:
    fridays = [d for d in range(1, 22) if _date(y, m, d).weekday() == 4]
    return _date(y, m, fridays[2] if len(fridays) > 2 else -1)


def _last_weekday(y: int, m: int) -> _date:
    d = _cal.monthrange(y, m)[1]
    while _date(y, m, d).weekday() > 4:
        d -= 1
    return _date(y, m, d)


class CalendarLoader:
    def __init__(self, csv_path: Path):
        self.manual: dict[str, str] = {}
        p = Path(csv_path)
        if p.exists():
            with open(p, newline="") as fh:
                for r in csv.DictReader(fh):
                    if r.get("date"):
                        self.manual[r["date"].strip()] = (r.get("reason") or "manual").strip()

    def check(self, session_date: str) -> CalendarDay:
        y, m, d = (int(x) for x in session_date.split("-"))
        dt = _date(y, m, d)
        if session_date in self.manual:
            reason = self.manual[session_date]
            if reason.lower() in ("none", "clear", "not_event"):
                return CalendarDay(session_date, False, "")   # operator override:
                # the computed rule (e.g. first-Friday NFP shifted by a holiday)
                # does not apply this date
            return CalendarDay(session_date, True, reason)
        if dt == _first_friday(y, m):
            return CalendarDay(session_date, True, "nfp")
        if m in (3, 6, 9, 12) and dt == _third_friday(y, m):
            return CalendarDay(session_date, True, "quarterly_opex")
        if dt == _last_weekday(y, m):
            return CalendarDay(session_date, True, "month_end_rebalance")
        return CalendarDay(session_date, False, "")

    def is_event_day(self, session_date: str) -> bool:
        return self.check(session_date).is_event_day
