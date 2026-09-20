"""Independent raw-bar outcome replay and scalar summary reconciliation."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from run import DATA, FLAGS
from study import digest, write_json


def main() -> None:
    receipt = json.loads((DATA / "analysis_receipt.json").read_text())
    for name, expected in receipt["outputs"].items():
        assert digest(Path(name)) == expected, name
    events = pd.read_parquet(DATA / "events.parquet")
    dates = pd.read_csv(DATA / "research_dates.csv").set_index("date")
    assert len(events) == 685 and not events.duplicated(["date", "known_min"]).any()
    native_rows = 0
    for date, entries in events.groupby("date"):
        meta = dates.loc[date]
        path = Path(meta.source_path)
        assert digest(path) == meta.source_sha256
        raw = pd.read_parquet(path).set_index("min")
        for event in entries.itertuples():
            t = event.known_min
            bars = raw.reindex(range(t, t + 60))
            assert (
                len(bars) == 60
                and bars[["open", "high", "low", "close"]].notna().all().all()
            )
            entry = float(bars.open.iloc[0])
            assert entry == event.entry_price and entry > meta.vol_trigger
            assert raw.loc[570 : t - 1, "low"].min() > meta.vol_trigger
            up = np.flatnonzero(bars.high.to_numpy() >= entry + 5)
            down = np.flatnonzero(bars.low.to_numpy() <= entry - 10)
            a, b = (int(up[0]) if len(up) else 61), (int(down[0]) if len(down) else 61)
            if a == b:
                outcome = "neither" if a == 61 else "ambiguous"
            else:
                outcome = "target_first" if a < b else "adverse_first"
            assert outcome == event.outcome, (date, t, outcome, event.outcome)
            if outcome == "neither":
                assert pd.isna(event.first_touch_min)
            else:
                assert event.first_touch_min == t + min(a, b)
            native_rows += len(bars)
    summary = pd.read_csv(DATA / "summary.csv")
    reconciled = 0
    for row in summary.itertuples():
        flag = FLAGS[row.cohort]
        cohort = events if flag is None else events[events[flag]]
        sample = []
        for event in cohort.to_dict("records"):
            if row.period != "pooled" and event["half"] != row.period:
                continue
            value = event["rvol"]
            state = (
                "unknown"
                if not np.isfinite(value)
                else "high"
                if value > 1
                else "ordinary"
            )
            if (
                row.state == "all"
                or row.state == state
                or (row.state == "observed" and state != "unknown")
            ):
                sample.append(event)
        assert len(sample) == row.n
        for label in ["target_first", "adverse_first", "neither", "ambiguous"]:
            assert sum(x["outcome"] == label for x in sample) == getattr(row, label)
        if sample:
            expected = (
                100 * sum(x["outcome"] == "target_first" for x in sample) / len(sample)
            )
            assert np.isclose(expected, row.rate)
        else:
            assert pd.isna(row.rate)
        reconciled += 1
    loo = pd.read_csv(DATA / "leave_one_date_out.csv")
    for row in loo.itertuples():
        flag = FLAGS[row.cohort]
        part = events if flag is None else events[events[flag]]
        part = part[part.date.ne(row.removed_date)]
        high = part[part.rvol.gt(1)]
        ordinary = part[part.rvol.le(1)]
        assert row.high_n == len(high) and row.ordinary_n == len(ordinary)
        hw = int(high.outcome.eq("target_first").sum())
        ow = int(ordinary.outcome.eq("target_first").sum())
        assert row.high_wins == hw and row.ordinary_wins == ow
        assert np.isclose(row.delta_pp, 100 * (hw / len(high) - ow / len(ordinary)))
    write_json(
        DATA / "verification.json",
        {
            "analysis_receipt_sha256": digest(DATA / "analysis_receipt.json"),
            "verifier_sha256": digest(Path(__file__)),
            "native_entries_replayed": len(events),
            "native_bar_observations": native_rows,
            "unique_native_dates": events.date.nunique(),
            "summary_rows_independently_recounted": reconciled,
            "leave_one_date_rows_recounted": len(loo),
            "outcomes_and_above_vt_match": True,
        },
    )
    print(
        "Verified",
        len(events),
        "native entry paths,",
        reconciled,
        "summary rows,",
        len(loo),
        "day deletions",
    )


if __name__ == "__main__":
    main()
