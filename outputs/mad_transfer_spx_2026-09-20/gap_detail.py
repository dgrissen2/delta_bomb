"""Outcome-free source-support reconciliation for already identified missing entries."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from prepare import DATA, REGISTRY, digest, save_json


def main() -> None:
    gaps = pd.read_parquet(DATA / "sector_gap_entries.parquet")
    roots = {s["symbol"]: Path(s["root"]) for s in json.loads(REGISTRY.read_text())}
    records, hashes = [], {}
    for (symbol, date), group in gaps.groupby(["symbol", "date"]):
        root = roots[symbol]
        manifest = root / "days" / symbol / f"{date}.json"
        if not manifest.exists():
            raise FileNotFoundError(f"No collection receipt: {manifest}")
        hashes[str(manifest)] = digest(manifest)
        meta = json.loads(manifest.read_text())
        path = root / "derived" / symbol / "sources" / f"{date}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"No source support table: {path}")
        hashes[str(path)] = digest(path)
        source = pd.read_parquet(path)
        for row in group.itertuples():
            window = source[source.minute.between(row.known_min-30, row.known_min-1)]
            strict = window.strict_iv.notna()
            recovered = window.recovered_iv.notna() & window.guard100.eq(True)
            records.append(dict(entry_id=row.entry_id, variant=row.variant, symbol=symbol,
                date=date, known_min=row.known_min, end_min=row.known_min-1, half=row.half,
                block=row.block, gap_cause=row.gap_cause, collection_status=meta["status"],
                selected_expirations=json.dumps(meta.get("selection", {}).get("expirations", [])),
                source_slots=len(window), strict_source_slots=int(strict.sum()),
                guarded_recovery_slots=int(recovered.sum()),
                unusable_source_slots=int((~(strict | recovered)).sum()),
                expiry_eligible_slots=int(window.expiry_eligible.eq(True).sum()),
                recovery_prior_ok_slots=int(window.recovery_prior_ok.eq(True).sum()),
                recovery_shock_slots=int(window.recovery_shock.eq(True).sum()),
                reported_window_slots=int(row.supported_slots),
                reported_unique_sources=int(row.unique_sources),
                interpretation="source support only; not a new fill or a native market-quote diagnosis"))
    detail = pd.DataFrame(records)
    if len(detail) != len(gaps) or detail.entry_id.isna().any():
        raise ValueError("Gap reconciliation incomplete")
    bracket = detail.gap_cause.eq("no_allowed_expiry_bracket")
    if not detail.loc[bracket, "selected_expirations"].eq("[]").all():
        raise ValueError("Missing-bracket cause contradicts listed-expiry selection")
    if np.isinf(detail.select_dtypes(include=[np.number])).any().any():
        raise ValueError("Invalid source diagnostics")
    detail.to_csv(DATA / "gap_source_support.csv", index=False)
    save_json(DATA / "gap_support_receipt.json", dict(input_hashes=hashes,
        output_sha256=digest(DATA / "gap_source_support.csv"), entries=len(detail),
        unique_instrument_endpoints=len(detail.drop_duplicates(["symbol", "date", "end_min"])),
        no_outcome_fields_read=True, no_refetch_or_policy_change=True,
        code_sha256=digest(Path(__file__))))
    print(f"Reconciled {len(detail)} missing ETF-entry slots", flush=True)


if __name__ == "__main__":
    main()
