"""Audit the complete dated VT population and freeze one outcome-blind day draw.

The default CLI audits only. ``--draw`` is an explicit operation after collection
has completed. No B06, sector coverage, or outcome data is read by this module.
"""

import argparse
import csv
from datetime import date, datetime, time
import hashlib
import json
from pathlib import Path
import random
import re
import secrets
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
CENTRAL = Path("/Users/dgrissen/Dev/central_trade_data")
DEFAULT_VT = Path(
    "/Users/dgrissen/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv"
)
DEFAULT_ORIGINAL = CENTRAL / "thetadata/spx_index_1m_ohlc"
DEFAULT_NEW = CENTRAL / "thetadata/sector_surface_b06_50d_2026-09-13-v1/spx_normalized"
DEFAULT_NOTES = Path("/Users/dgrissen/Dev/sg_note_scraper/founders_notes/articles")
DEFAULT_MANIFEST = HERE.parent / "branch_b_above_vt_10d_2026-09-12/manifest.json"
AS_OF = date(2026, 9, 11)
ET = ZoneInfo("America/New_York")
CAVEAT = (
    "Same-date pre-open publication labels support availability, not contemporaneous local "
    "ingestion. The corrected VT CSV and saved notes do not preserve captured-at/revision "
    "history. Legacy minute files discard raw timestamps; their interval-start interpretation "
    "is inherited from the original study. No future note or carried-forward VT is admitted."
)


def sha256(path: Path) -> str:
    """Hash a complete local input without changing it."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _load_levels(path: Path) -> list[dict[str, Any]]:
    levels: dict[str, dict[str, Any]] = {}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for line, row in enumerate(reader, start=2):
            day = date.fromisoformat(row["Date"])
            if day.year != 2026 or day > AS_OF:
                continue
            key = day.isoformat()
            if key in levels:
                raise ValueError(f"Duplicate VT date {key}; no arbitrary last-row selection")
            try:
                value = float(row["Vol Trigger"])
            except (TypeError, ValueError):
                value = float("nan")
            levels[key] = {
                "date": key, "vol_trigger": value if np.isfinite(value) else None,
                "vt_csv_line": line,
            }
    return [levels[day] for day in sorted(levels)]


def _cells(line: str) -> list[str]:
    return [cell.strip().replace("**", "") for cell in line.strip().strip("|").split("|")]


def inspect_note(path: Path, day: str) -> dict[str, Any]:
    """Read only the note publication header and explicitly labeled SPX VT table cell."""
    lines = path.read_text().splitlines()
    header = next((line for line in lines if line.strip()), "")
    metadata = next((line for line in lines[:10] if line.startswith("**Date:**")), "")
    result: dict[str, Any] = {
        "path": str(path), "sha256": sha256(path), "header": header,
        "publication_extract": metadata, "publication_time_as_labeled": None,
        "publication_timezone": "America/New_York", "preopen": False,
        "spx_vol_triggers": [], "table_extracts": [], "publication_parse_error": None,
    }
    try:
        parsed = datetime.strptime(metadata.removeprefix("**Date:**").strip(),
                                   "%A, %B %d, %Y at %I:%M %p")
        match = re.search(
            r"([A-Za-z]+\s+\d{1,2},\s+\d{4}\s+at\s+\d{1,2}:\d{2}\s+[AP]M)"
            r"\s+(ET|EST|EDT)\b", header, re.IGNORECASE,
        )
        if match is None:
            raise ValueError("First heading has no explicit Eastern publication label")
        header_time = datetime.strptime(match[1].upper(), "%B %d, %Y at %I:%M %p")
        if parsed != header_time or parsed.date().isoformat() != day:
            raise ValueError("Publication metadata/header/session dates or times conflict")
        aware = parsed.replace(tzinfo=ET)
        if match[2].upper() in {"EST", "EDT"} and match[2].upper() != aware.tzname():
            raise ValueError("Explicit Eastern timezone conflicts with calendar DST")
        result["publication_time_as_labeled"] = aware.isoformat()
        result["preopen"] = parsed.time() < time(9, 30)
    except ValueError as exc:
        result["publication_parse_error"] = str(exc)

    spx_column: int | None = None
    for number, line in enumerate(lines, start=1):
        if not line.lstrip().startswith("|"):
            spx_column = None
            continue
        cells = _cells(line)
        if "SPX" in cells:
            spx_column = cells.index("SPX")
        if spx_column is None or not re.search(r"vol(?:atility)?\s+trigger", cells[0], re.I):
            continue
        if spx_column >= len(cells):
            continue
        cleaned = cells[spx_column].replace("$", "").replace(",", "").strip()
        try:
            value = float(cleaned)
        except ValueError:
            continue
        if np.isfinite(value) and value > 0:
            result["spx_vol_triggers"].append(value)
            result["table_extracts"].append({"line": number, "extract": line})
    result["spx_vol_triggers"] = sorted(set(result["spx_vol_triggers"]))
    return result


def inspect_spx(frame: pd.DataFrame, day: str) -> dict[str, Any]:
    """Validate exact observed RTH labels, OHLC and native timestamps when retained."""
    result: dict[str, Any] = {
        "status": "invalid_spx", "complete": False, "rth_rows": 0,
        "spot_open": None, "missing_minutes": [], "detail": None,
    }
    required = {"min", "open", "high", "low", "close"}
    if not required <= set(frame.columns):
        result["detail"] = "Missing native minute/OHLC columns"
        return result
    try:
        minutes = pd.to_numeric(frame["min"], errors="raise").to_numpy(dtype=float)
        if not np.isfinite(minutes).all() or not (minutes == np.floor(minutes)).all():
            raise ValueError("Invalid/fractional native minute labels")
        if "timestamp" in frame:
            stamps = pd.to_datetime(frame["timestamp"], errors="raise")
            if stamps.dt.tz is None:
                raise ValueError("Native timestamps have no timezone")
            stamps = stamps.dt.tz_convert(ET)
            if (not stamps.dt.strftime("%Y-%m-%d").eq(day).all()
                    or not (stamps.dt.second.eq(0) & stamps.dt.microsecond.eq(0)
                            & stamps.dt.nanosecond.eq(0)).all()
                    or not np.array_equal(stamps.dt.hour * 60 + stamps.dt.minute, minutes)):
                raise ValueError("Native timestamps disagree with session/minute labels")
        rth = frame.loc[(minutes >= 570) & (minutes < 960)].copy()
        rth["min"] = minutes[(minutes >= 570) & (minutes < 960)].astype(int)
        result["rth_rows"] = len(rth)
        if rth["min"].duplicated().any():
            raise ValueError("Duplicate RTH minute labels")
        values = rth[["open", "high", "low", "close"]].to_numpy(dtype=float)
        if (not np.isfinite(values).all() or not (values > 0).all()
                or not (rth.high >= rth[["open", "close", "low"]].max(axis=1)).all()
                or not (rth.low <= rth[["open", "close", "high"]].min(axis=1)).all()):
            raise ValueError("Invalid native OHLC")
        result["missing_minutes"] = sorted(set(range(570, 960)) - set(rth["min"]))
        opening = rth.loc[rth["min"].eq(570), "open"]
        result["spot_open"] = float(opening.iloc[0]) if len(opening) else None
        result["complete"] = len(rth) == 390 and not result["missing_minutes"]
        result["status"] = "complete" if result["complete"] else "incomplete_spx"
    except (TypeError, ValueError, AttributeError) as exc:
        result["detail"] = str(exc)
    return result


def _spx_source(day: str, old: Path, new: Path,
                hashes: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    for root in (old, new):
        path = root / f"{day}.parquet"
        if not path.exists():
            attempts.append({"path": str(path), "status": "missing_spx", "complete": False})
            continue
        hashes[str(path)] = sha256(path)
        try:
            item = inspect_spx(pd.read_parquet(path), day)
        except (OSError, ValueError) as exc:
            item = {"status": "invalid_spx", "complete": False, "detail": str(exc),
                    "spot_open": None, "rth_rows": 0}
        item.update({"path": str(path), "sha256": hashes[str(path)]})
        attempts.append(item)
        if item["complete"]:
            return item, attempts
    existing = [item for item in attempts if item["status"] != "missing_spx"]
    selected = existing[-1] if existing else {
        "status": "missing_spx", "complete": False, "path": "", "sha256": "",
        "spot_open": None, "rth_rows": 0,
    }
    return selected, attempts


def build_population(vt_path: Path, original_spx: Path, normalized_spx: Path, notes_root: Path,
                     original_manifest: Path) -> tuple[pd.DataFrame, dict[str, Any], dict[str, str]]:
    """Audit every dated 2026 VT session without writing files or drawing dates."""
    levels = _load_levels(vt_path)
    original_dates = set(json.loads(original_manifest.read_text())["selected_dates"])
    hashes = {str(path): sha256(path) for path in (vt_path, original_manifest)}
    records, sessions = [], []
    for level in levels:
        day, vt = level["date"], level["vol_trigger"]
        notes = [inspect_note(path, day) for path in sorted(notes_root.glob(f"{day}_*/article.md"))]
        hashes.update({item["path"]: item["sha256"] for item in notes})
        preopen_values = {value for item in notes if item["preopen"]
                          for value in item["spx_vol_triggers"]}
        if preopen_values and preopen_values != {vt}:
            note_status = "conflicting_preopen_vt"
        elif preopen_values == {vt}:
            note_status = "matching_preopen_note"
        else:
            note_status = "missing_matching_preopen_note"
        source, attempts = _spx_source(day, original_spx, normalized_spx, hashes)
        positive_vt = vt is not None and vt > 0
        above = bool(positive_vt and source.get("spot_open") is not None
                     and source["spot_open"] > vt)
        reasons = []
        if not positive_vt:
            reasons.append("invalid_vt")
        if note_status != "matching_preopen_note":
            reasons.append(note_status)
        if not source["complete"]:
            reasons.append(source["status"])
        if source.get("spot_open") is not None and positive_vt and not above:
            reasons.append("open_not_above_vt")
        if day in original_dates:
            reasons.append("original_exploration_day")
        record = {**level, "spot_open": source.get("spot_open"), "above_vt_at_open": above,
                  "complete_spx": source["complete"], "rth_rows": source.get("rth_rows", 0),
                  "spx_path": source["path"], "source_path": source["path"],
                  "source_sha256": source.get("sha256", ""),
                  "vt_provenance_status": note_status,
                  "original_exploration_day": day in original_dates,
                  "eligible": not reasons, "exclusion_reasons": "|".join(reasons)}
        records.append(record)
        sessions.append({**level, "status": note_status, "notes": notes, "spx_attempts": attempts})
    provenance = {"publication_vs_capture_caveat": CAVEAT, "sessions": sessions,
                  "duplicate_policy": "Reject duplicate dated CSV rows before drawing",
                  "vt_note_policy": "All parseable same-date pre-open SPX VT cells must match CSV"}
    return pd.DataFrame(records), provenance, hashes


def _write_frozen(path: Path, content: str) -> None:
    try:
        with path.open("x") as handle:
            handle.write(content)
    except FileExistsError:
        if path.read_text() != content:
            raise ValueError(f"Existing frozen artifact differs: {path}") from None


def freeze_sample(ledger: pd.DataFrame, provenance: dict[str, Any], hashes: dict[str, str],
                  output: Path, count: int = 50) -> pd.DataFrame:
    """Store one 64-bit seed and immutable draw; fail on changed inputs or artifacts."""
    if ledger.date.duplicated().any():
        raise ValueError("Duplicate ledger dates")
    eligible = sorted(ledger.loc[ledger.eligible, "date"].tolist())
    if count <= 0 or len(eligible) < count:
        raise ValueError(f"Only {len(eligible)} eligible dates; requested {count}; no draw created")
    ledger_csv = ledger.sort_values("date").to_csv(index=False)
    fingerprint = hashlib.sha256(_json({
        "ledger_csv": ledger_csv, "provenance": provenance, "source_hashes": hashes,
        "sample_count": count, "algorithm": "random.Random(seed).sample(sorted_dates, count)",
    }).encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    seed_path = output / "sampling_seed.json"
    if seed_path.exists():
        seed_record = json.loads(seed_path.read_text())
    else:
        seed_record = {"seed": str(secrets.randbits(64)), "seed_bits": 64,
                       "inputs_sha256": fingerprint, "count": count}
        _write_frozen(seed_path, _json(seed_record))
    if seed_record["inputs_sha256"] != fingerprint or seed_record["count"] != count:
        raise ValueError("Inputs differ from frozen seed; refuse to reroll or change the population")
    seed = int(seed_record["seed"])
    if not 0 <= seed < 2**64:
        raise ValueError("Invalid frozen 64-bit seed")
    order = random.Random(seed).sample(eligible, count)
    rank = {day: index for index, day in enumerate(order, start=1)}
    selected = ledger.loc[ledger.date.isin(order)].sort_values("date").copy()
    selected.insert(1, "random_draw_rank", selected.date.map(rank))
    selected = selected.reset_index(drop=True)
    draw_table = selected.sort_values("random_draw_rank")
    payload = {
        "as_of": AS_OF.isoformat(), "sample_count": count, "population_count": len(ledger),
        "eligible_additional_count": len(eligible), "eligible_dates": eligible,
        "seed": str(seed), "seed_bits": 64, "inputs_sha256": fingerprint,
        "algorithm": f"random.Random(seed).sample(sorted eligible dates, {count})",
        "draw_order": order, "selected_dates": sorted(order), "source_hashes": hashes,
        "publication_vs_capture_caveat": provenance.get("publication_vs_capture_caveat", CAVEAT),
        "no_replacement_policy": "Retain sampled dates regardless of B06 or option coverage/outcomes",
        "exclusion_reason_counts": ledger.loc[~ledger.eligible, "exclusion_reasons"]
            .str.split("|").explode().value_counts().to_dict(),
    }
    artifacts = {
        "population_ledger.csv": ledger_csv,
        "selected_days.csv": selected.to_csv(index=False),
        "random_draw_order.csv": draw_table.to_csv(index=False),
        "vt_note_provenance.json": _json(provenance),
        "sampling_input_hashes.json": _json(hashes),
        "sampling_manifest.json": _json(payload),
    }
    for name, content in artifacts.items():
        _write_frozen(output / name, content)
    return selected


def require_completed_coverage(path: Path) -> str:
    """Prevent a draw while the full-population coverage retrieval is still running."""
    if not path.exists() or json.loads(path.read_text()).get("status") != "complete":
        raise ValueError("Coverage collection must be complete before drawing")
    return sha256(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vt", type=Path, default=DEFAULT_VT)
    parser.add_argument("--original-spx", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--normalized-spx", type=Path, default=DEFAULT_NEW)
    parser.add_argument("--notes", type=Path, default=DEFAULT_NOTES)
    parser.add_argument("--original-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=HERE)
    parser.add_argument("--draw", action="store_true", help="Freeze one draw after coverage completion")
    args = parser.parse_args()
    ledger, provenance, hashes = build_population(
        args.vt, args.original_spx, args.normalized_spx, args.notes, args.original_manifest,
    )
    for path in (Path(__file__).resolve(), HERE / "PROTOCOL.md"):
        hashes[str(path)] = sha256(path)
    coverage = HERE / "spx_coverage_download.json"
    if coverage.exists():
        hashes[str(coverage)] = sha256(coverage)
    summary = {"dated_vt_sessions": len(ledger), "complete_spx": int(ledger.complete_spx.sum()),
               "above_vt_complete": int((ledger.complete_spx & ledger.above_vt_at_open).sum()),
               "eligible_additional": int(ledger.eligible.sum()),
               "note_status_counts": ledger.vt_provenance_status.value_counts().to_dict(),
               "draw_requested": args.draw}
    if args.draw:
        hashes[str(coverage)] = require_completed_coverage(coverage)
        selected = freeze_sample(ledger, provenance, hashes, args.output)
        summary["sampled_dates"] = selected.date.tolist()
    print(_json(summary), end="")


if __name__ == "__main__":
    main()
