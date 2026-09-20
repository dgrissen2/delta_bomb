"""Publish fixed result tables and provenance without changing source artifacts."""

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from combined import DATA, OUT, digest, write_json


def markdown(frame: pd.DataFrame) -> str:
    """Render a plain table without an optional formatting dependency."""
    lines = ["| " + " | ".join(frame.columns) + " |", "|" + "---|" * len(frame.columns)]
    for row in frame.itertuples(index=False, name=None):
        cells = [
            "—" if pd.isna(v) else f"{v:.2f}" if isinstance(v, float) else str(v)
            for v in row
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    verification = json.loads((DATA / "verification.json").read_text())
    assert verification["all_checks_passed"]
    receipt = json.loads((DATA / "analysis_receipt.json").read_text())
    for path, expected in receipt["outputs"].items():
        assert digest(Path(path)) == expected, path
    summary = pd.read_csv(DATA / "summary.csv")
    text = [
        "# Complete combined-expansion result tables\n\nPercentages and percentage-point differences; whole-date 95% bootstrap intervals.\n2026 H2 is partial. No adjustments for prior selection or between-date dependence.\n"
    ]
    for policy in ["all", "first", "spaced60"]:
        columns = [
            "dataset",
            "period",
            "n",
            "target_first",
            "adverse_first",
            "neither",
            "ambiguous",
            "rate",
            "low",
            "high",
            "days",
            "research_days",
            "median_per_research_day",
            "median_per_active_day",
            "delta_vs_reference_pp",
            "delta_low",
            "delta_high",
        ]
        text.append(
            f"\n## {policy}\n\n"
            + markdown(summary[summary.policy.eq(policy)][columns])
            + "\n"
        )
    for filename in [
        "policy_changes.csv",
        "added_route_patterns.csv",
        "novel_dates.csv",
    ]:
        text.append(
            f"\n## {filename}\n\n" + markdown(pd.read_csv(DATA / filename)) + "\n"
        )
    (OUT / "ALL_RESULTS.md").write_text("".join(text))
    files = []
    for path in sorted(DATA.iterdir()):
        if not path.is_file() or path.name == "inventory.json":
            continue
        rows = (
            pq.ParquetFile(path).metadata.num_rows
            if path.suffix == ".parquet"
            else len(pd.read_csv(path))
            if path.suffix == ".csv"
            else None
        )
        files.append(
            dict(
                path=str(path),
                sha256=digest(path),
                bytes=path.stat().st_size,
                rows=rows,
            )
        )
    write_json(
        DATA / "inventory.json",
        dict(
            files=files,
            project_files={
                str(p): digest(p)
                for p in sorted(OUT.iterdir())
                if p.suffix in [".py", ".md"]
            },
            payload_bytes_excluding_inventory=sum(p["bytes"] for p in files),
            provider_calls=0,
            independent_review=False,
        ),
    )
    print(
        f"Registered {len(files)} central files; all source hashes and verification passed."
    )


if __name__ == "__main__":
    main()
