"""Render complete tables and fixed descriptive decompositions, without tuning."""

from pathlib import Path

import numpy as np
import pandas as pd

from study import DATA, OUT, digest, write_json


def markdown(frame: pd.DataFrame) -> str:
    def cell(value: object) -> str:
        if isinstance(value, float):
            return f"{value:.4f}" if np.isfinite(value) else "unestimable"
        return str(value).replace("|", "/")

    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join(["---"] * len(frame.columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(cell(x) for x in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    )
    return "\n".join(lines)


def main() -> None:
    added = pd.read_csv(DATA / "addition_overlap.csv")
    added["hit"] = added.outcome.eq("target_first")
    novel = (
        added.groupby(["candidate", "new_date"])
        .agg(n=("date", "size"), wins=("hit", "sum"), days=("date", "nunique"))
        .reset_index()
    )
    novel["rate"] = 100 * novel.wins / novel.n
    novel.to_csv(DATA / "novel_date_diagnostic.csv", index=False)
    events = pd.read_parquet(DATA / "executions.parquet")
    routes = (
        events[events.dataset.eq("persistence_added")]
        .groupby(["sector_persist_state", "spx_persist_state"])
        .size()
        .rename("n")
        .reset_index()
    )
    routes.to_csv(DATA / "persistence_routes.csv", index=False)
    names = [
        "summary.csv",
        "policy_changes.csv",
        "day_influence_summary.csv",
        "volume_summary.csv",
        "volume_cross.csv",
        "volume_within_block.csv",
        "volume_context_balance.csv",
        "novel_date_diagnostic.csv",
        "persistence_routes.csv",
    ]
    text = [
        "# Complete fixed-comparison tables",
        "",
        "All rates and interval endpoints are percentages; deltas are percentage points.",
        "Unestimable means no supported interval/value, not zero. All intervals are exploratory.",
        "Added-only rows are thinned on their own for description; actual union policy changes",
        "are in policy_changes.csv and must not be inferred by adding standalone spaced rows.",
        "",
    ]
    for name in names:
        text.extend(["## " + name, "", markdown(pd.read_csv(DATA / name)), ""])
    (OUT / "ALL_RESULTS.md").write_text("\n".join(text))
    paths = [
        OUT / "FINDINGS.md",
        OUT / "ALL_RESULTS.md",
        OUT / "SHORT_DATED_SKEW_PILOT.md",
        DATA / "novel_date_diagnostic.csv",
        DATA / "persistence_routes.csv",
    ]
    write_json(
        DATA / "report_receipt.json",
        {
            "outputs": {str(p): digest(p) for p in paths},
            "report_code_hash": digest(Path(__file__)),
            "scope": "Formatting existing comparisons; retrospective new-date diagnostics are not entry gates",
        },
    )
    print("Saved full tables and report receipt", flush=True)


if __name__ == "__main__":
    main()
