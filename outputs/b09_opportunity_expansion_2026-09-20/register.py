"""Inventory central artifacts and record the completed validation package."""

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from study import DATA, OUT, digest, write_json


def main() -> None:
    for receipt_name, key in [
        ("analysis_receipt.json", "outputs"),
        ("report_receipt.json", "outputs"),
    ]:
        receipt = json.loads((DATA / receipt_name).read_text())
        for path, expected in receipt[key].items():
            assert digest(Path(path)) == expected, path
    record = json.loads((DATA / "verification.json").read_text())
    assert record["all_hashes_verified"]
    rows = []
    for path in sorted(DATA.iterdir()):
        if not path.is_file() or path.name == "inventory.json":
            continue
        n = (
            pq.ParquetFile(path).metadata.num_rows
            if path.suffix == ".parquet"
            else len(pd.read_csv(path))
            if path.suffix == ".csv"
            else None
        )
        rows.append(
            {
                "path": str(path),
                "sha256": digest(path),
                "bytes": path.stat().st_size,
                "rows": n,
            }
        )
    code_docs = {
        str(p): digest(p) for p in sorted(OUT.iterdir()) if p.suffix in [".py", ".md"]
    }
    write_json(
        DATA / "inventory.json",
        {
            "files": rows,
            "project_files": code_docs,
            "payload_bytes_excluding_inventory": sum(r["bytes"] for r in rows),
            "provider_calls": 0,
            "new_skew_measurements": 0,
            "independent_review": "New execution not independently reviewed; separate main-thread proposal review completed",
        },
    )
    print(
        f"Inventoried {len(rows)} central files and {len(code_docs)} project files",
        flush=True,
    )


if __name__ == "__main__":
    main()
