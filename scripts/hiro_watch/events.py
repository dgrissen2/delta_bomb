"""Event-day policy (owner decision 2026-09-09): the engine stands down ONLY on FOMC decision days.
Every other event day — NFP, quarterly opex, month-end rebalance, CPI — is TRADED and tagged here
so results can be sliced after the fact.

The frozen v1 engine (R4.4) stands down on any date its CalendarLoader flags: computed NFP /
quarterly-opex / month-end, plus rows in `docs/hiro_engine/event_calendar.csv`. That CSV supports an
operator override (`not_event`), so the policy is applied as DATA: this module writes the CSV with
every FOMC decision day as `fomc` and every computed event date as `not_event`. No engine line
changes; CONFIG_HASH is untouched (the CSV is not part of the hash).

    python hiro_watch/events.py            rewrite docs/hiro_engine/event_calendar.csv (2026-08-12 .. 2027-12-31)
    tag("2026-09-04") -> "nfp"             reporting tag ("" on a plain day)

Sources: FOMC — federalreserve.gov/monetarypolicy/fomccalendars.htm (decision day = 2nd day);
CPI — bls.gov/schedule/news_release/cpi.htm (2026 only; extend when BLS posts 2027).
"""
from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hiro_engine.calendar import CalendarLoader          # noqa: E402  (frozen; read-only use)

REPO = Path(__file__).resolve().parents[2]
CALENDAR_CSV = REPO / "docs/hiro_engine/event_calendar.csv"
START, END = date(2026, 8, 12), date(2027, 12, 31)

FOMC = {  # decision days
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
    "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08",
}
CPI = {  # 08:30 release days
    "2026-01-13", "2026-02-13", "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12",
    "2026-09-11", "2026-10-14", "2026-11-10", "2026-12-10",
}
_COMPUTED = CalendarLoader(Path("/nonexistent"))       # no CSV → computed rules only


def tag(session_date: str) -> str:
    """Reporting tag for a session: fomc | cpi | nfp | quarterly_opex | month_end_rebalance | ''."""
    if session_date in FOMC:
        return "fomc"
    if session_date in CPI:
        return "cpi"
    return _COMPUTED.check(session_date).reason


def rows(start: date = START, end: date = END) -> list[tuple[str, str]]:
    out = []
    d = start
    while d <= end:
        s = d.isoformat()
        if s in FOMC:
            out.append((s, "fomc"))
        elif d.weekday() < 5 and _COMPUTED.check(s).is_event_day:
            out.append((s, "not_event"))              # traded; tagged by tag()
        d += timedelta(days=1)
    return out


def write(path: Path = CALENDAR_CSV) -> int:
    r = rows()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "reason"])
        w.writerows(r)
    return len(r)


if __name__ == "__main__":
    n = write()
    print(f"{CALENDAR_CSV}: {n} rows ({sum(1 for _, r in rows() if r == 'fomc')} fomc, rest not_event)")
