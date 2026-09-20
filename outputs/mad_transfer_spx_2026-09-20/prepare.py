"""Verify frozen measurements and create memberships without loading price outcomes."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from logic import RULES, classify, endpoint_join, or_states

OUT = Path(__file__).resolve().parent
ROOT = Path("/Users/dgrissen/Dev/central_trade_data/thetadata")
DATA = ROOT / "mad_transfer_spx_2026-09-20-v1"
REGISTRY = OUT.parent / "sector_iv_mad_remaining_2025_2026_2026-09-19/all_sector_sources.json"
SPX = ROOT / "spx_iv_mad_2024_2026_2026-09-20-v1"
SCORE = ROOT / "branch_b_stop10_2026-09-19-v1/event_outcomes.parquet"
DAYS = ROOT / "branch_b_2024_halfyear_2026-09-19-v1/selected_days.csv"
PREVIOUS = ROOT / "b09_mad_grid_2026-09-19-v1"
SYMBOLS = sorted(["XLC", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI", "XLB", "XLRE", "XLK", "XLU"])
HALVES = ["2025_H1", "2025_H2", "2026_H1", "2026_H2"]
PERIODS = ["pooled", "completed"] + HALVES
MODES = ["all", "first", "spaced60"]


def digest(path: Path) -> str:
    """Hash inputs without interpreting outcome columns."""
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def save_json(path: Path, value: dict) -> None:
    """Write a provenance receipt with finite JSON values only."""
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def period_rows(frame: pd.DataFrame, period: str) -> pd.DataFrame:
    if period == "pooled":
        return frame
    return frame[frame.half.isin(HALVES[:3])] if period == "completed" else frame[frame.half.eq(period)]


def verify_file(path: Path, expected: str, hashes: dict) -> None:
    if digest(path) != expected:
        raise ValueError(f"Changed registered source: {path}")
    hashes[str(path)] = expected


def check_measurement(scores: pd.DataFrame, bases: pd.DataFrame, symbol: str) -> None:
    """Validate every scale/date ledger and every usable source window."""
    if not bases.status.eq("ok").all() or not bases.lookback_end.lt(bases.date).all():
        raise ValueError(f"Historical baseline not ready: {symbol}")
    for row in bases.itertuples():
        history = json.loads(row.source_dates)
        if len(history) != row.history_days or len(set(history)) != len(history) \
                or not all(row.lookback_start <= d <= row.lookback_end < row.date for d in history):
            raise ValueError("Invalid historical date ledger")
    available = scores.signed_score.notna()
    good = scores[available]
    if not np.isfinite(good[["b1", "b2", "acceleration", "scale"]]).all().all() \
            or not good.scale.gt(0).all():
        raise ValueError("Invalid scored arithmetic")
    np.testing.assert_allclose(good.signed_score, -good.acceleration / good.scale)
    np.testing.assert_allclose(good.acceleration, (good.b2 - good.b1) / 15, atol=1e-14)
    np.testing.assert_array_equal(scores.block, (scores.end_min - 570) // 60)
    for row in good.itertuples():
        minutes = json.loads(row.source_minutes)
        if row.start_min != row.end_min - 29 or len(minutes) != len(set(minutes)) \
                or not all(row.start_min <= m <= row.end_min for m in minutes):
            raise ValueError("Current measurement violates its causal window")


def coverage_tables(events: pd.DataFrame, membership: pd.DataFrame,
                    sectors: pd.DataFrame, spx: pd.DataFrame) -> None:
    """Publish support/participation by half and endpoint block before outcomes."""
    records, valid_records, instrument_records = [], [], []
    for (variant, half, block, rule), group in membership.groupby(
            ["variant", "half", "block", "rule"]):
        c = group.state.value_counts()
        records.append(dict(variant=variant, half=half, block=block, rule=rule, n=len(group),
                            **{x: int(c.get(x, 0)) for x in ["yes", "no", "unknown"]}))
    for keys, group in events.groupby(["variant", "half", "block", "valid_sectors"]):
        valid_records.append(dict(zip(["variant", "half", "block", "valid_sectors"], keys))
                             | dict(n=len(group), days=int(group.date.nunique())))
    for data in [sectors, spx]:
        for keys, group in data.groupby(["variant", "half", "block", "symbol"]):
            instrument_records.append(dict(zip(["variant", "half", "block", "symbol"], keys))
                                      | dict(n=len(group), observed=int(group.signed_score.notna().sum())))
    pd.DataFrame(records).to_csv(DATA / "pre_outcome_participation.csv", index=False)
    pd.DataFrame(valid_records).to_csv(DATA / "valid_sector_counts.csv", index=False)
    pd.DataFrame(instrument_records).to_csv(DATA / "instrument_coverage.csv", index=False)


def check_freeze() -> dict:
    freeze = json.loads((DATA / "freeze.json").read_text())
    for path, expected in (freeze["input_hashes"] | freeze["code_hashes"] |
                           freeze["output_hashes"]).items():
        if digest(Path(path)) != expected:
            raise ValueError(f"Frozen file changed: {path}")
    return freeze


def main() -> None:
    if DATA.exists():
        raise FileExistsError(f"Refusing to replace prepared study: {DATA}")
    hashes = {str(p): digest(p) for p in [REGISTRY, DAYS, OUT / "PROTOCOL.md"]}
    for name in ["REVIEW_RESPONSE.md", "CHARLIE_PROPOSAL.md", "CLAUDE_STRATEGY_RECHECK.md"]:
        p = OUT.parent / "b09_mad_followup_plan_2026-09-20" / name
        hashes[str(p)] = digest(p)
    sources = json.loads(REGISTRY.read_text())
    if sorted(s["symbol"] for s in sources) != SYMBOLS:
        raise ValueError("Sector universe changed")
    for source in sources:
        for path, expected in source["files"].items():
            verify_file(Path(path), expected, hashes)
    spx_summary = SPX / "calibration_exact/SPXW/summary.json"
    hashes[str(spx_summary)] = digest(spx_summary)
    for path, expected in json.loads(spx_summary.read_text())["output_hashes"].items():
        verify_file(Path(path), expected, hashes)
    for p in [SPX / "calibration_exact/SPXW/verification_final.json",
              SPX / "endpoint_pairing_verification.json", SPX / "gap_diagnostics.json"]:
        hashes[str(p)] = digest(p)
    expected = json.loads((SCORE.parent / "score_verification.json").read_text())["hashes"][str(SCORE)]
    verify_file(SCORE, expected, hashes)
    keys = ["date", "variant", "known_min", "signal_min", "always_above", "cohort", "event_id"]
    candidates = pd.read_parquet(SCORE, columns=keys)
    candidates = candidates[candidates.variant.isin(["b09", "b07", "b05"])
                            & candidates.cohort.ne("development_10")
                            & candidates.date.between("2025-01-01", "2026-09-18")]
    days = pd.read_csv(DAYS, float_precision="round_trip")
    days = days[days.cohort.ne("development_10") & days.date.between("2025-01-01", "2026-09-18")]
    if days.date.duplicated().any() or len(days) != 239:
        raise ValueError("Research-date population changed")
    vt_checks = []
    for day in days.itertuples():
        path = Path(day.source_path)
        verify_file(path, day.source_sha256, hashes)
        price = pd.read_parquet(path).set_index("min").loc[570:959]
        if price.index.tolist() != list(range(570, 960)):
            raise ValueError("Incomplete native SPX minute session")
        entries = candidates[candidates.date.eq(day.date)]
        for minute, group in entries.groupby("known_min"):
            opening = float(price.loc[minute, "open"])
            prior_min = float(price.loc[570:minute-1, "low"].min())
            strict = opening > day.vol_trigger and prior_min > day.vol_trigger
            if not group.always_above.eq(strict).all():
                raise ValueError("Causal above-VT flag mismatch")
            vt_checks.append(dict(date=day.date, known_min=minute, entry_open=opening,
                                  prior_low=prior_min, vol_trigger=day.vol_trigger,
                                  strict_above=bool(strict), candidate_rows=len(group)))
    events = candidates[candidates.always_above].sort_values(["date", "known_min", "event_id"])
    events = events.drop_duplicates(["variant", "date", "known_min"]).reset_index(drop=True)
    expected_counts = {"b05": 1537, "b07": 415, "b09": 3141}
    if events.variant.value_counts().to_dict() != expected_counts:
        raise ValueError("Parent event counts changed")
    events["entry_id"] = events.variant + "|" + events.date + "|" + events.known_min.astype(str)
    events["half"] = events.date.str[:4] + "_H" + np.where(
        events.date.str[5:7].astype(int) <= 6, "1", "2")
    frames = []
    for source in sources:
        scores = pd.read_parquet(next(p for p in source["files"] if p.endswith("/scored_windows.parquet")))
        bases = pd.read_parquet(next(p for p in source["files"] if p.endswith("/block_baselines.parquet")))
        check_measurement(scores, bases, source["symbol"])
        joined = endpoint_join(events[["entry_id", "date", "known_min", "half", "variant"]], scores)
        if joined.symbol.isna().any():
            raise ValueError("Expected sector endpoint row absent")
        daily = pd.read_parquet(next(p for p in source["files"] if p.endswith("/daily_coverage.parquet")))
        joined = joined.merge(daily[["date", "status"]].rename(columns={"status": "day_status"}),
                              on="date", how="left", validate="many_to_one")
        frames.append(joined)
        print(f"Verified and joined {source['symbol']}", flush=True)
    sectors = pd.concat(frames, ignore_index=True)
    matrices = {field: sectors.pivot(index="entry_id", columns="symbol", values=field)
                .reindex(index=events.entry_id, columns=SYMBOLS).to_numpy()
                for field in ["signed_score", "acceleration", "b2"]}
    events["valid_sectors"] = np.logical_and.reduce(
        [np.isfinite(x) for x in matrices.values()]).sum(axis=1)
    events["all11"] = events.valid_sectors.eq(11)
    events["block"] = (events.known_min - 1 - 570) // 60
    members = []
    for rule in RULES:
        state, yes, unknown = classify(matrices["signed_score"], matrices["acceleration"],
                                       matrices["b2"], rule)
        block = events[["entry_id", "variant", "date", "known_min", "half", "block"]].copy()
        block["rule"], block["state"] = rule, state
        block["qualifying_votes"], block["unknown_votes"] = yes, unknown
        members.append(block)
    spx_scores = pd.read_parquet(SPX / "calibration_exact/SPXW/scored_windows.parquet")
    spx_bases = pd.read_parquet(SPX / "calibration_exact/SPXW/block_baselines.parquet")
    check_measurement(spx_scores, spx_bases, "SPXW")
    b09 = events[events.variant.eq("b09")]
    spx = endpoint_join(b09[["entry_id", "date", "known_min", "half", "variant"]], spx_scores)
    if spx.symbol.isna().any():
        raise ValueError("SPX endpoint clock does not cover B09")
    state, yes, unknown = classify(spx.signed_score.to_numpy()[:, None],
                                   spx.acceleration.to_numpy()[:, None],
                                   spx.b2.to_numpy()[:, None], "F4", breadth=1)
    block = b09[["entry_id", "variant", "date", "known_min", "half", "block"]].copy()
    block["rule"], block["state"] = "SPX_F", state
    block["qualifying_votes"], block["unknown_votes"] = yes, unknown
    members.append(block)
    f4 = members[1].set_index("entry_id").state.reindex(b09.entry_id).to_numpy()
    union = block.copy()
    union["rule"], union["state"] = "OR_F4_SPX", or_states(f4, state)
    union[["qualifying_votes", "unknown_votes"]] = -1  # OR has no basket vote count.
    members.append(union)
    cross = b09[["entry_id", "date", "half", "block"]].copy()
    cross["sector_state"], cross["spx_state"] = f4, state
    cross["joint_measurable"] = (f4 != "unknown") & (state != "unknown")
    events["joint_measurable"] = events.entry_id.map(cross.set_index("entry_id").joint_measurable).eq(True)
    memberships = pd.concat(members, ignore_index=True)
    gaps = sectors[sectors.signed_score.isna()].copy()
    gaps["gap_cause"] = np.where(gaps.day_status.eq("missing_tenor_bracket"),
                                 "no_allowed_expiry_bracket",
                                 np.where(gaps.day_status.eq("captured"),
                                          "captured_but_current_window_rejected",
                                          "recorded_day_status:" + gaps.day_status.fillna("absent")))
    DATA.mkdir(parents=True)
    events.to_parquet(DATA / "event_keys.parquet", index=False)
    days.to_csv(DATA / "research_dates.csv", index=False)
    sectors.to_parquet(DATA / "sector_at_entry.parquet", index=False)
    spx.to_parquet(DATA / "spx_at_entry.parquet", index=False)
    memberships.to_parquet(DATA / "memberships.parquet", index=False)
    cross.to_parquet(DATA / "spx_cross_keys.parquet", index=False)
    gaps.to_parquet(DATA / "sector_gap_entries.parquet", index=False)
    gaps.groupby(["variant", "symbol", "half", "gap_cause"], dropna=False).agg(
        entries=("entry_id", "size"), days=("date", "nunique")).reset_index().to_csv(
            DATA / "gap_causes.csv", index=False)
    pd.DataFrame(vt_checks).to_csv(DATA / "native_vt_checks.csv", index=False)
    coverage_tables(events, memberships, sectors, spx)
    freeze = dict(at=datetime.now(timezone.utc).isoformat(), input_hashes=hashes,
                  code_hashes={str(p): digest(p) for p in OUT.glob("*.py")},
                  output_hashes={str(p): digest(p) for p in DATA.iterdir() if p.is_file()},
                  outcome_columns_loaded=False, counts=expected_counts, research_dates=len(days),
                  already_inspected_controls="B09 sign4 and sign_falling4 disclosed by Claude recheck",
                  new_cells="4 transfers + 6 controls (2 inspected), plus SPX rule/OR; B09 S4/F4 references")
    save_json(DATA / "freeze.json", freeze)
    print(json.dumps({"frozen": str(DATA), "parents": expected_counts,
                      "spx_states": block.state.value_counts().to_dict()}), flush=True)


if __name__ == "__main__":
    main()
