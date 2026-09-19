"""Recalculate the fixed four IV policies without changing the original fifty days."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
import pandas as pd

from collect import OUT, OLD, SYMBOLS, digest, emit, freeze_json, write_json
from iv_rules import ARCHIVE, SOURCE_SHA256, add_quality, make_surface, slopes, classify
from iv_rules import check_guard_boundaries

sys.path.insert(0, str(OLD))
spec = importlib.util.spec_from_file_location("frozen_replication", OLD / "replication.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
spec = importlib.util.spec_from_file_location("frozen_surface", OLD / "surface.py")
surface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(surface)
VARIANTS = ["original", "midpoint", "guarded_100", "guarded_50"]
FEATURE_COLUMNS = ["date", "episode_id", "parent_min", "symbol", "variant", "available",
                   "samples", "first_slope", "second_slope", "acceleration", "falling",
                   "accelerating"]
EPS = 1e-12


def safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [safe(v) for v in value]
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def verify_hashes(hashes: dict[str, str]) -> None:
    for path, expected in hashes.items():
        if digest(Path(path)) != expected:
            raise ValueError(f"Frozen source changed: {path}")


def parent_stage() -> None:
    """Freeze all parent identities before computing any new outcome."""
    if (OUT / "parent_freeze.json").exists():
        verify_hashes(json.loads((OUT / "parent_freeze.json").read_text())["hashes"])
        emit("parents_already_frozen")
        return
    old_days = pd.read_csv(OLD / "selected_days.csv")
    new_days = pd.read_csv(OUT / "selected_days.csv")
    if len(old_days) != 50 or len(new_days) != 100 or set(old_days.date) & set(new_days.date):
        raise ValueError("Combined sample must be fifty plus 100 disjoint dates")
    days = pd.concat([old_days.assign(cohort="original_50"),
                      new_days.assign(cohort="additional_100")], ignore_index=True)
    days = days.sort_values("date").reset_index(drop=True)
    if not days.date.is_unique or len(days) != 150:
        raise ValueError("Combined sample changed")
    records = []
    inputs = {}
    for row in days.itertuples(index=False):
        path = Path(row.source_path)
        if digest(path) != row.source_sha256:
            raise ValueError(f"SPX source changed: {path}")
        inputs[str(path)] = row.source_sha256
        parents = legacy.parents_for_day(row.date, path)
        records.append(parents.assign(cohort=row.cohort))
    parents = pd.concat(records, ignore_index=True)
    if not parents.episode_id.is_unique:
        raise ValueError("Duplicate parent")
    old = pd.read_csv(OLD / "b06_parents.csv", float_precision="round_trip").set_index("episode_id")
    reproduction = parents[parents.cohort.eq("original_50")].set_index("episode_id").loc[old.index]
    if len(reproduction) != len(old) or len(old) != 374:
        raise ValueError("Original parent population differs")
    for column in ["date", "parent_min", "parent_price", "boundary"]:
        np.testing.assert_equal(reproduction[column].to_numpy(), old[column].to_numpy())
    days.to_csv(OUT / "combined_days.csv", index=False)
    parents.to_csv(OUT / "b06_parents.csv", index=False)
    counts = parents.groupby("date").size()
    days[["date", "cohort"]].assign(n_b06=days.date.map(counts).fillna(0).astype(int)).to_csv(
        OUT / "day_event_counts.csv", index=False)
    for path in [OUT / "PROTOCOL.md", OUT / "combined_days.csv", OUT / "b06_parents.csv",
                 OUT / "selected_days.csv", OLD / "selected_days.csv",
                 OLD / "replication.py", OLD / "b06_signals.py", OLD / "signals.py",
                 OLD / "screen.py", OLD / "surface.py", ARCHIVE, Path(__file__),
                 OUT / "iv_rules.py"]:
        inputs[str(path)] = digest(path)
    freeze_json(OUT / "parent_freeze.json", {"hashes": inputs, "parents": len(parents),
                "days": 150, "original_parents_reproduced": 374})
    emit("parents_frozen", parents=len(parents), old=374, additional=len(parents)-374,
         active_days=int(parents.date.nunique()))


def ready_jobs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    jobs, missing = [], []
    old_days = pd.read_csv(OLD / "selected_days.csv").date.tolist()
    for day in old_days:
        for symbol in SYMBOLS:
            path = OLD / "surfaces" / f"{day}_{symbol}.json"
            if path.exists():
                meta = json.loads(path.read_text())
                jobs.append({"date": day, "symbol": symbol, "inputs": meta["signature"]["inputs"],
                             "original_surface": meta["path"], "cohort": "original_50"})
            else:
                missing.append({"date": day, "symbol": symbol, "reason": "missing_tenor_bracket",
                                "cohort": "original_50"})
    collection_path = OUT / "collection_manifest.json"
    if not collection_path.exists():
        return jobs, missing, False
    collection = json.loads(collection_path.read_text())
    new_dates = pd.read_csv(OUT / "selected_days.csv").date.tolist()
    if collection["dates"] != new_dates or collection["symbols"] != SYMBOLS:
        raise ValueError("Collection universe differs")
    pairs = {(p["date"], p["symbol"], p["expiration"]): p for p in collection["pairs"]}
    if len(pairs) != len(collection["pairs"]):
        raise ValueError("Duplicate collected expiry pair")
    for selection in collection["selections"]:
        day, symbol = selection["date"], selection["symbol"]
        if not selection["expirations"]:
            missing.append({"date": day, "symbol": symbol, "reason": selection["status"],
                            "cohort": "additional_100"})
            continue
        wanted = [pairs.get((day, symbol, e)) for e in selection["expirations"]]
        if any(p is None or p["status"] != "ok" for p in wanted):
            missing.append({"date": day, "symbol": symbol, "reason": "incomplete_input_pairs",
                            "cohort": "additional_100"})
            continue
        files = [f for p in wanted for f in p["files"]]
        if len(files) != 2 * len(wanted):
            raise ValueError("Endpoint pair incomplete")
        jobs.append({"date": day, "symbol": symbol,
                     "inputs": {f["path"]: f["sha256"] for f in files},
                     "original_surface": None, "cohort": "additional_100"})
    return jobs, missing, collection["status"] in {"complete", "complete_with_errors"}


def sector_job(job: dict[str, Any], parents: pd.DataFrame,
               implementation: dict[str, str]) -> dict[str, Any]:
    day, symbol = job["date"], job["symbol"]
    base = OUT / "sector_features" / f"{day}_{symbol}"
    meta_path = base.with_suffix(".json")
    signature = {"inputs": job["inputs"], "implementation": implementation,
                 "parents_sha256": digest(OUT / "b06_parents.csv")}
    if meta_path.exists():
        previous = json.loads(meta_path.read_text())
        if previous["signature"] != signature:
            raise ValueError("Sector feature input/implementation changed")
        verify_hashes(job["inputs"])
        if previous["status"] == "ok":
            verify_hashes(previous["artifacts"])
        return previous
    verify_hashes(job["inputs"])
    iv, greeks = [], []
    for path in job["inputs"]:
        (iv if "implied_volatility" in path else greeks).append(pd.read_parquet(path))
    try:
        prepared = surface._prepare(pd.concat(iv, ignore_index=True),
                                    pd.concat(greeks, ignore_index=True))
        prepared = add_quality(prepared)
        grid = pd.date_range(day + " 09:30", periods=300, freq="min", tz="America/New_York")
        original, _ = make_surface(prepared, "valid", grid)
        midpoint, _ = make_surface(prepared, "mid_valid", grid)
    except ValueError as exc:
        result = {"date": day, "symbol": symbol, "cohort": job["cohort"],
                  "status": "invalid_source", "error": str(exc), "signature": signature}
        write_json(meta_path, result)
        return result
    series = {"original": original.iv, "midpoint": midpoint.iv,
              "guarded_100": midpoint.iv.where(midpoint.guard100),
              "guarded_50": midpoint.iv.where(midpoint.guard50)}
    if job["original_surface"]:
        saved = pd.read_parquet(job["original_surface"]).set_index("timestamp").atm
        np.testing.assert_allclose(original.iv.to_numpy(), saved.to_numpy(),
                                   rtol=0, atol=1e-10, equal_nan=True)
    causal_checked = False
    if (day, symbol) in {("2026-01-06", "XLRE"), ("2026-01-28", "XLF"),
                         ("2025-02-06", "XLRE"), ("2025-02-06", "XLK")}:
        cutoff = pd.Timestamp(day + " 10:15", tz="America/New_York")
        prefix = prepared[prepared.timestamp.le(cutoff)].copy()
        test, _ = make_surface(add_quality(prefix), "mid_valid", grid[grid <= cutoff])
        for col in ["iv", "max_width", "prior_ok", "shock", "guard100", "guard50"]:
            np.testing.assert_allclose(test[col].to_numpy(dtype=float),
                                       midpoint.loc[test.index, col].to_numpy(dtype=float),
                                       rtol=0, atol=1e-10, equal_nan=True)
        causal_checked = True
    features, coverage = [], []
    events = parents[parents.date.eq(day)]
    for variant, values in series.items():
        valid = values.notna()
        coverage.append({"date": day, "symbol": symbol, "cohort": job["cohort"],
                         "variant": variant, "valid_minutes": int(valid.sum()),
                         "recovered_minutes": int((valid & original.iv.isna()).sum()),
                         "lost_original_minutes": int((~valid & original.iv.notna()).sum())})
        for event in events.itertuples(index=False):
            positions = np.arange(event.parent_min-35-570, event.parent_min-5-570)
            if len(positions) != 30 or positions.min() < 0 or positions.max() >= 300:
                raise ValueError("Reference window outside collected native data")
            window = values.iloc[positions].to_numpy()
            available = bool(np.isfinite(window).all())
            first, second, acceleration = slopes(window)
            features.append({"date": day, "episode_id": event.episode_id,
                "parent_min": event.parent_min, "symbol": symbol, "variant": variant,
                "available": available, "samples": int(np.isfinite(window).sum()),
                "first_slope": first, "second_slope": second, "acceleration": acceleration,
                "falling": bool(available and second < -EPS),
                "accelerating": bool(available and second < -EPS and acceleration < -EPS)})
    feature_path = base.with_suffix(".parquet")
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(features, columns=FEATURE_COLUMNS).to_parquet(feature_path, index=False)
    minute_path = OUT / "minute_series" / f"{day}_{symbol}.parquet"
    minute_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(series).rename_axis("timestamp").reset_index().to_parquet(minute_path, index=False)
    result = {"date": day, "symbol": symbol, "cohort": job["cohort"], "status": "ok",
              "signature": signature, "path": str(feature_path), "coverage": coverage,
              "original_reproduced": bool(job["original_surface"]),
              "causal_checked": causal_checked,
              "artifacts": {str(p): digest(p) for p in [feature_path, minute_path]}}
    write_json(meta_path, result)
    return result


def feature_stage(watch: bool) -> None:
    """Process complete immutable panels while collection continues, without outcomes."""
    freeze = json.loads((OUT / "parent_freeze.json").read_text())
    verify_hashes(freeze["hashes"])
    implementation = {str(p): digest(p) for p in [Path(__file__), OUT / "iv_rules.py",
                                                 OLD / "surface.py", ARCHIVE]}
    parents = pd.read_csv(OUT / "b06_parents.csv", float_precision="round_trip")
    records: dict[tuple[str, str], dict[str, Any]] = {}
    emit("guard_tests", passed=check_guard_boundaries(), frozen_function_source=SOURCE_SHA256)
    while True:
        jobs, missing, complete = ready_jobs()
        pending = [j for j in jobs if (j["date"], j["symbol"]) not in records]
        if pending:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(sector_job, job, parents, implementation) for job in pending]
                for future in as_completed(futures):
                    result = future.result()
                    records[(result["date"], result["symbol"])] = result
                    if len(records) % 50 == 0 or result["status"] != "ok":
                        emit("features", complete=len(records), available_jobs=len(jobs),
                             status=result["status"], date=result["date"], symbol=result["symbol"])
        write_json(OUT / "feature_progress.json",
                   {"completed": len(records), "collection_complete": complete,
                    "missing_panels": len(missing), "at": datetime.now(timezone.utc).isoformat()})
        if complete:
            break
        if not watch:
            raise ValueError("Collection not complete; use --watch to wait without outcomes")
        time.sleep(5)
    invalid = [r for r in records.values() if r["status"] != "ok"]
    successful = [r for r in records.values() if r["status"] == "ok"]
    frames = [pd.read_parquet(r["path"]) for r in successful]
    feature = pd.concat(frames, ignore_index=True)
    expected = pd.MultiIndex.from_tuples([
        (e.date, e.episode_id, e.parent_min, s, v)
        for e in parents.itertuples(index=False) for s in SYMBOLS for v in VARIANTS],
        names=["date", "episode_id", "parent_min", "symbol", "variant"])
    feature = feature.set_index(list(expected.names)).reindex(expected).reset_index()
    for col in ["available", "falling", "accelerating"]:
        feature[col] = feature[col].fillna(False).astype(bool)
    feature.samples = feature.samples.fillna(0).astype(int)
    basket = feature.groupby(["variant", "date", "episode_id", "parent_min"]).agg(
        coverage=("available", "sum"), falling_count=("falling", "sum"),
        accelerating_count=("accelerating", "sum")).reset_index()
    basket["missing"] = 11 - basket.coverage
    for kind in ["falling", "accelerating"]:
        basket[kind + "_state"] = [classify(int(k), int(m))
                                   for k, m in zip(basket[kind + "_count"], basket.missing)]
    if len(feature) != len(parents)*44 or len(basket) != len(parents)*4:
        raise ValueError("Feature population changed")
    original_dates = set(pd.read_csv(OLD / "selected_days.csv").date)
    original_features = pd.read_csv(OLD / "sector_event_features.csv", float_precision="round_trip")
    original_features = original_features[original_features.descriptor.eq("atm")]
    ours = feature[feature.variant.eq("original") & feature.date.isin(original_dates)]
    check = ours.merge(original_features, on=["date", "episode_id", "parent_min", "symbol"],
                       validate="one_to_one", suffixes=("_ours", "_saved"))
    if len(check) != 374*11 or not check.available_ours.eq(check.available_saved).all():
        raise ValueError("Original sector availability differs")
    np.testing.assert_allclose(check.acceleration_ours, check.acceleration_saved,
                               rtol=0, atol=1e-10, equal_nan=True)
    archived = json.loads(ARCHIVE.read_text())["results"]
    old_summary = {}
    for variant in VARIANTS:
        b = basket[basket.variant.eq(variant) & basket.date.isin(original_dates)]
        for kind in ["falling", "accelerating"]:
            for state in ["yes", "no", "unknown"]:
                count = int(b[kind + "_state"].eq(state).sum())
                expected_n = archived["OUTCOME_SUMMARIES"][variant+"_"+kind+"_"+state]["n"]
                if count != expected_n:
                    raise ValueError("Original policy classification count differs")
                old_summary[variant+"_"+kind+"_"+state] = count
    feature.to_parquet(OUT / "sector_event_features.parquet", index=False)
    basket.to_csv(OUT / "basket_before_outcomes.csv", index=False)
    coverage = pd.DataFrame([c for r in successful for c in r["coverage"]])
    coverage.to_csv(OUT / "surface_coverage.csv", index=False)
    missing_frame = pd.DataFrame(missing + [
        {"date": r["date"], "symbol": r["symbol"], "reason": r["status"],
         "cohort": r["cohort"], "detail": r["error"]} for r in invalid])
    missing_frame.to_csv(OUT / "missing_panels.csv", index=False)
    raw_hashes = {}
    artifact_hashes = {}
    for result in records.values():
        raw_hashes.update(result["signature"]["inputs"])
        artifact_hashes.update(result.get("artifacts", {}))
    verify_hashes(raw_hashes)
    verify_hashes(implementation)
    paths = [OUT / "sector_event_features.parquet", OUT / "basket_before_outcomes.csv",
             OUT / "surface_coverage.csv", OUT / "missing_panels.csv",
             OUT / "collection_manifest.json", OUT / "parent_freeze.json"]
    freeze_json(OUT / "feature_freeze_before_outcomes.json", {
        "hashes": {str(p): digest(p) for p in paths} | implementation,
        "raw_hashes": raw_hashes, "sector_artifact_hashes": artifact_hashes,
        "successful_panels": len(successful), "missing_panels": len(missing_frame),
        "original_panels_reproduced": sum(r["original_reproduced"] for r in successful),
        "causal_prefix_checks": sum(r["causal_checked"] for r in successful),
        "original_classifications_reproduced": old_summary,
        "parents": len(parents), "sector_features": len(feature), "basket_features": len(basket),
        "at": datetime.now(timezone.utc).isoformat()})
    emit("features_frozen_before_outcomes", parents=len(parents), panels=len(successful),
         missing=len(missing_frame), raw_inputs=len(raw_hashes))


def describe(frame: pd.DataFrame) -> dict[str, Any]:
    counts = frame.outcome.value_counts()
    return {"signals": len(frame), "active_days": int(frame.date.nunique()),
            **{k: int(counts.get(k, 0)) for k in
               ["target_first", "adverse_first", "neither", "ambiguous"]},
            "hit_rate": float(frame.outcome.eq("target_first").mean()) if len(frame) else None}


def analyze_stage() -> None:
    """Join unchanged price scores only after the feature archive has been frozen."""
    frozen = json.loads((OUT / "feature_freeze_before_outcomes.json").read_text())
    verify_hashes(frozen["hashes"])
    verify_hashes(frozen["raw_hashes"])
    verify_hashes(json.loads((OUT / "parent_freeze.json").read_text())["hashes"])
    parents = pd.read_csv(OUT / "b06_parents.csv", float_precision="round_trip")
    days = pd.read_csv(OUT / "combined_days.csv")
    baskets = pd.read_csv(OUT / "basket_before_outcomes.csv")
    results = []
    for day, group in parents.groupby("date"):
        source = Path(group.source_path.iloc[0])
        raw = pd.read_parquet(source)
        for event in group.itertuples(index=False):
            score = legacy.score_path(raw, event.parent_min, event.parent_price)
            results.append({"date": day, "episode_id": event.episode_id,
                            "parent_min": event.parent_min, "cohort": event.cohort, **score})
    outcomes = pd.DataFrame(results)
    expected = pd.read_csv(OLD / "event_paths.csv", float_precision="round_trip")
    comparison = outcomes[outcomes.cohort.eq("original_50")].merge(
        expected[["episode_id", "outcome"]], on="episode_id", validate="one_to_one",
        suffixes=("_new", "_old"))
    if len(comparison) != 374 or not comparison.outcome_new.eq(comparison.outcome_old).all():
        raise ValueError("Original outcomes differ")
    outcomes.to_csv(OUT / "event_paths.csv", index=False)
    joined = baskets.merge(outcomes, on=["date", "episode_id", "parent_min"], validate="many_to_one")
    joined.to_csv(OUT / "event_ledger.csv", index=False)
    cohorts = {"original_50": days.loc[days.cohort.eq("original_50"), "date"].tolist(),
               "additional_100": days.loc[days.cohort.eq("additional_100"), "date"].tolist(),
               "combined_150": days.date.tolist(),
               "year_2025": days.loc[days.date.str.startswith("2025"), "date"].tolist(),
               "year_2026": days.loc[days.date.str.startswith("2026"), "date"].tolist()}
    tables, intervals, states, daily_rows = [], {}, [], []
    for cohort, dates in cohorts.items():
        base = outcomes[outcomes.date.isin(dates)]
        groups = {"baseline": base}
        for variant in VARIANTS:
            b = joined[joined.date.isin(dates) & joined.variant.eq(variant)]
            groups[variant] = b[b.accelerating_state.eq("yes")]
            for kind in ["falling", "accelerating"]:
                for state in ["yes", "no", "unknown"]:
                    states.append({"cohort": cohort, "variant": variant, "condition": kind,
                                   "state": state, **describe(b[b[kind+"_state"].eq(state)])})
        base_rate = describe(base)["hit_rate"]
        rng = np.random.default_rng(20260919)
        draws = rng.integers(0, len(dates), size=(10000, len(dates)))
        rates = {}
        for variant, frame in groups.items():
            desc = describe(frame)
            tables.append({"cohort": cohort, "sampled_days": len(dates), "variant": variant,
                           **desc, "uplift_pp": 100*(desc["hit_rate"]-base_rate)
                           if desc["hit_rate"] is not None else None})
            daily = frame.assign(target=frame.outcome.eq("target_first")).groupby("date").agg(
                n=("episode_id", "size"), targets=("target", "sum")).reindex(dates, fill_value=0)
            for day, row in daily.iterrows():
                daily_rows.append({"cohort": cohort, "variant": variant, "date": day,
                                   "signals": int(row.n), "targets": int(row.targets)})
            data = daily[["n", "targets"]].to_numpy(dtype=float)
            totals = data[draws].sum(axis=1)
            rates[variant] = np.divide(totals[:, 1], totals[:, 0],
                                      out=np.full(10000, np.nan), where=totals[:, 0] > 0)
        for variant in VARIANTS:
            diff = 100*(rates[variant] - rates["baseline"])
            valid = np.isfinite(diff)
            intervals[cohort+"__"+variant] = {
                "estimate_pp": 100*(describe(groups[variant])["hit_rate"]-base_rate)
                if len(groups[variant]) else None,
                "interval_pp": np.quantile(diff[valid], [.025, .975]).tolist()
                if valid.any() else None,
                "defined_draws": int(valid.sum()), "draws": 10000, "seed": 20260919}
    table = pd.DataFrame(tables)
    archived = json.loads(ARCHIVE.read_text())["results"]["OUTCOME_SUMMARIES"]
    for row in table[table.cohort.eq("original_50")].itertuples(index=False):
        prior = archived["all" if row.variant == "baseline" else row.variant+"_accelerating_yes"]
        if (row.signals, row.target_first, row.adverse_first, row.neither, row.active_days) != (
                prior["n"], prior["targets"], prior["adverse"], prior["neither"], prior["days"]):
            raise ValueError("Original five-row table differs")
    table.to_csv(OUT / "comparison_table.csv", index=False)
    pd.DataFrame(states).to_csv(OUT / "state_summary.csv", index=False)
    pd.DataFrame(daily_rows).to_csv(OUT / "daily_counts.csv", index=False)
    write_json(OUT / "paired_date_bootstrap.json", safe(intervals))
    paths = [OUT / name for name in ["event_paths.csv", "event_ledger.csv",
             "comparison_table.csv", "state_summary.csv", "daily_counts.csv",
             "paired_date_bootstrap.json"]]
    verify_hashes(frozen["hashes"])
    verify_hashes(frozen["raw_hashes"])
    write_json(OUT / "verification.json", {
        "original_five_rows_reproduced": True, "old_parents": 374,
        "additional_parents": int(outcomes.cohort.eq("additional_100").sum()),
        "total_parents": len(outcomes), "sampled_days": len(days),
        "source_hashes_unchanged": len(frozen["raw_hashes"]),
        "outcome_artifacts": {str(p): digest(p) for p in paths},
        "feature_freeze_sha256": digest(OUT / "feature_freeze_before_outcomes.json"),
        "at": datetime.now(timezone.utc).isoformat()})
    emit("results", table=safe(table.to_dict(orient="records")), intervals=safe(intervals))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["parents", "features", "analyze"])
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    if args.stage == "features":
        feature_stage(args.watch)
    else:
        {"parents": parent_stage, "analyze": analyze_stage}[args.stage]()
