"""Archive completed study data centrally without changing frozen file contents."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from collect import OUT, DATA, digest, write_json


def move_verified(source: Path, target: Path) -> dict[str, Any]:
    """Replace a project data file with a byte-identical central link."""
    if source.is_symlink():
        if source.resolve() != target.resolve():
            raise ValueError(f"Unexpected data link: {source}")
    else:
        expected = digest(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if digest(target) != expected:
                raise ValueError(f"Refusing to overwrite different central data: {target}")
            source.unlink()
        else:
            source.rename(target)
        source.symlink_to(target)
        if digest(source) != expected:
            raise ValueError("Archived contents changed")
    return {"project_alias": str(source), "central_path": str(target),
            "bytes": target.stat().st_size, "sha256": digest(target)}


def main() -> None:
    """Require final verification, archive data, then measure the completed inventory."""
    if json.loads((OUT / "collection_manifest.json").read_text())["status"] != "complete":
        raise ValueError("Collection must complete before final archival")
    verification = json.loads((OUT / "verification.json").read_text())
    for path, expected in verification["outcome_artifacts"].items():
        if digest(Path(path)) != expected:
            raise ValueError("Outcome artifact changed before archival")
    records = []
    for source in sorted(OUT.iterdir()):
        if source.is_file() and source.suffix in {".csv", ".parquet", ".json", ".jsonl", ".log"}:
            records.append(move_verified(source, DATA / "research" / source.name))
    write_json(DATA / "archive_manifest.json", {"at": datetime.now(timezone.utc).isoformat(),
        "scope": "Completed study data and logs; code/findings remain in delta_bomb",
        "files": records, "bytes": sum(r["bytes"] for r in records),
        "file_count": len(records)})
    for path, expected in verification["outcome_artifacts"].items():
        if digest(Path(path)) != expected:
            raise ValueError("Outcome artifact changed during archival")
    directories = ["index_history_ohlc", "spx_normalized", "option_list_contracts",
                   "option_history_greeks_implied_volatility",
                   "option_history_greeks_first_order", "derived/sector_features",
                   "derived/minute_series", "research"]
    inventory = {}
    for name in directories:
        files = sorted(p for p in (DATA / name).rglob("*") if p.is_file())
        parquets = [p for p in files if p.suffix == ".parquet"]
        inventory[name] = {"files": len(files), "bytes": sum(p.stat().st_size for p in files),
                           "parquet_files": len(parquets),
                           "parquet_rows": sum(pq.ParquetFile(p).metadata.num_rows for p in parquets)}
    root_files = sorted(p for p in DATA.iterdir() if p.is_file()
                        and p.name not in {"inventory.json", "README.md", "DATA_DICTIONARY.md"})
    inventory["root_provenance"] = {"files": len(root_files),
                                  "bytes": sum(p.stat().st_size for p in root_files)}
    requests = [json.loads(line) for line in (DATA / "requests.jsonl").read_text().splitlines()]
    started = [r for r in requests if r["status"] == "started"]
    errors = [r for r in requests if r["status"] == "error"]
    attempted_keys = Counter(r["key"] for r in started)
    if max(attempted_keys.values(), default=0) > 2:
        raise ValueError("Attempt ceiling violated")
    totals = {"files": sum(r["files"] for r in inventory.values()),
              "bytes": sum(r["bytes"] for r in inventory.values())}
    result = {"at": datetime.now(timezone.utc).isoformat(), "directories": inventory,
        "totals": totals, "scope": "Data, logs and provenance; excludes README, data dictionary and this inventory",
        "api_requests_started": len(started), "distinct_request_keys_started": len(attempted_keys),
        "started_by_method": dict(Counter(r["method"] for r in started)),
        "request_status_counts": dict(Counter(r["status"] for r in requests)),
        "maximum_attempts_per_key": max(attempted_keys.values(), default=0),
        "historical_errors": len(errors),
        "authentication_errors": sum("UNAUTHENTICATED" in str(r).upper() for r in errors),
        "collection_status": "complete", "sampled_days": 150, "new_days": 100,
        "parents": verification["total_parents"], "final_outcome_hashes": verification["outcome_artifacts"]}
    write_json(DATA / "inventory.json", result)
    print(json.dumps({"central_root": str(DATA), "archived_files": len(records),
                      "inventory": result}, default=str))


if __name__ == "__main__":
    main()
