"""LevelsLoader (R2.3): parse the SG levels CSV, fail closed.

Valid only if the CSV row carries the session date AND CW - VT > 0.
The historical CSV has no implied-move column; IM is None unless supplied live
(R2.5 straddle fallback) => R3.4 returns CHOP in backtests. NEVER read any
`Ref Px`-style price column from SpotGamma exports.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from .models import Levels


def _f(v: str) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class LevelsLoader:
    def __init__(self, csv_path: Path):
        self.csv_path = Path(csv_path)

    def load(self, session_date: str, im: Optional[float] = None) -> Levels:
        row = None
        if self.csv_path.exists():
            with open(self.csv_path, newline="") as fh:
                for r in csv.DictReader(fh):
                    if r.get("Date") == session_date:
                        row = r          # last matching row wins (file is append-ordered)
        if row is None:
            return Levels(date=session_date, vt=None, cw=None, sg_index=None, im=im, valid=False)
        vt, cw = _f(row.get("Vol Trigger")), _f(row.get("Call Wall"))
        valid = vt is not None and cw is not None and (cw - vt) > 0
        return Levels(date=session_date, vt=vt, cw=cw, sg_index=_f(row.get("sg_index")),
                      im=im, valid=valid)
