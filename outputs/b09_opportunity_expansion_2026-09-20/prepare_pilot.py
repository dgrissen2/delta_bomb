"""Prepare an outcome-blind measurement calendar; do not fetch or score skew."""

import json

import numpy as np
import pandas as pd

from study import DATA, HALVES, OUT, SYMBOLS, digest, write_json


def main() -> None:
    dates = pd.read_csv(DATA / "research_dates.csv", usecols=["date"])
    dates["half"] = dates.date.map(lambda d: f"{d[:4]}_H{(int(d[5:7]) - 1) // 6 + 1}")
    rng = np.random.default_rng(20260920)
    selected = []
    for half, count in zip(HALVES, [3, 3, 3, 1], strict=True):
        pool = sorted(dates.loc[dates.half.eq(half), "date"])
        selected.extend(
            {"date": str(d), "half": half}
            for d in rng.choice(pool, count, replace=False)
        )
    pd.DataFrame(selected).sort_values("date").to_csv(
        DATA / "skew_pilot_dates.csv", index=False
    )
    write_json(
        DATA / "skew_pilot_preparation.json",
        {
            "status": "Prepared only; no provider calls, new skew measurements or outcome test",
            "calendar": selected,
            "selection": "Seed20260920, 3/3/3/1 dates by half, no outcome inputs",
            "calendar_source_hash": digest(DATA / "research_dates.csv"),
            "symbols": SYMBOLS,
            "proposed_tenor_calendar_days": 7,
            "coordinates": ["ATM", "+25-delta call", "-25-delta put diagnostic"],
            "raw_minutes_et": "09:30 through14:29, one minute; scores10:00 through14:30 entry times",
            "constituent_phase": "Top3 prior-published holding weights per ETF per pilot date, measurement only",
            "readiness": {
                "existing_sector_surface_selection": "30-calendar-day target, permitted8–65DTE brackets",
                "seven_day_surface": "Not certified by existing caches; native contract/quote inventory needed",
                "constituent_membership": "Dated sector-ETF holdings and publication timing not yet verified",
                "local_IVV_weights": "Existing historical IVV weights are not interchangeable with each sector ETF holdings",
            },
            "design_path": str(OUT / "SHORT_DATED_SKEW_PILOT.md"),
            "script_hash": digest(OUT / "prepare_pilot.py"),
        },
    )
    print(json.dumps(selected), flush=True)


if __name__ == "__main__":
    main()
