"""Freeze signal-time far/near calls, retaining deterministic selection failures."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

try:
    from scripts.pandar_hypothesis_api import DATA, ROOT, Orats, ticker_batches
except ModuleNotFoundError:
    from pandar_hypothesis_api import DATA, ROOT, Orats, ticker_batches

OUT = ROOT / "outputs/pandar_hypothesis_2026-09-07"


def select_contracts(rows: list[dict[str, Any]], signal_date: str, *, delta_min: float = .02,
                     delta_max: float = .10, target_delta: float = .05,
                     minimum_otm_pct: float = 0) -> dict[str, Any]:
    """Pick an expiry/strike once by distance and delta, never by later price."""
    result: dict[str, Any] = {"selection_status": "missing_signal_chain"}
    if not rows:
        return result
    frame = pd.DataFrame(rows)
    required = {"expirDate", "strike", "delta", "stockPrice"}
    if not required <= set(frame):
        return result | {"selection_status": "missing_chain_fields"}
    frame["calendar_dte"] = (pd.to_datetime(frame.expirDate) - pd.Timestamp(signal_date)).dt.days
    frame = frame[frame.calendar_dte.between(7, 14)].copy()
    if frame.empty:
        return result | {"selection_status": "no_expiry_in_dte_band"}
    frame["expiry_distance"] = abs(frame.calendar_dte - 10)
    chosen = frame.sort_values(["expiry_distance", "expirDate"]).iloc[0].expirDate
    result.update(expiry=str(chosen))
    chain = frame[frame.expirDate.eq(chosen)].sort_values("strike").copy()
    if chain.strike.duplicated().any():
        return result | {"selection_status": "duplicate_contract_identity"}
    calls = chain[chain.delta.between(delta_min, delta_max) & chain.strike.gt(chain.stockPrice)
                  & (100 * (chain.strike / chain.stockPrice - 1) >= minimum_otm_pct)].copy()
    if calls.empty:
        return result | {"selection_status": "no_call_in_delta_band"}
    calls["delta_distance"] = abs(calls.delta - target_delta)
    far = calls.sort_values(["delta_distance", "strike"]).iloc[0]
    result.update(far_strike=float(far.strike), signal_delta=float(far.delta),
                  signal_spot=float(far.stockPrice), signal_bid=float(far.callBidPrice),
                  signal_ask=float(far.callAskPrice), signal_calendar_dte=int(far.calendar_dte),
                  signal_otm_pct=100 * (float(far.strike / far.stockPrice) - 1))
    lowers = chain[chain.strike.lt(far.strike)]
    if lowers.empty:
        return result | {"selection_status": "no_adjacent_nearer_strike"}
    near = lowers.iloc[-1]
    result.update(near_strike=float(near.strike), signal_near_delta=float(near.delta))
    if near.strike <= near.stockPrice:
        return result | {"selection_status": "nearer_not_otm"}
    return result | {"selection_status": "selected", "right": "C",
                     "deliverable_status": "pending_exact_reference_verification"}


def freeze_signal_contracts() -> None:
    """Retrieve batched signal chains only, save all choices before outcome histories."""
    population_path = OUT / "selected_population.csv"
    population = pd.read_csv(population_path)
    protocol = ROOT / "hypothesis_tracking/pandar_seed_and_frozen_protocol.md"
    source_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in (population_path, protocol)}
    prefetch = OUT / "before_signal_chains.json"
    if not prefetch.exists():
        prefetch.write_text(json.dumps({"created_at": datetime.now(UTC).isoformat(),
                                        "source_hashes": source_hashes}, indent=2))
    else:
        if json.loads(prefetch.read_text())["source_hashes"] != source_hashes:
            raise ValueError("frozen population/protocol changed; start a new specification")
    client = Orats()
    all_rows, choices = [], []
    date_column = "tradeDate" if "tradeDate" in population else "signal_date"
    for signal, group in population.groupby(date_column, sort=True):
        for batch in ticker_batches(group.ticker.tolist()):
            rows = client.get("hist/strikes", {"ticker": ",".join(batch), "tradeDate": signal,
                                              "dte": "1,35"}, "signal_chain")
            all_rows.extend(rows)
            for ticker in batch:
                selected = select_contracts([row for row in rows if row.get("ticker") == ticker],
                                            signal)
                poprow = group[group.ticker.eq(ticker)].iloc[0].to_dict()
                choices.append(poprow | selected)
        print(json.dumps({"signal": signal, "choices_so_far": len(choices)}), flush=True)
    DATA.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows).to_parquet(DATA / "signal_chains.parquet", index=False)
    result = pd.DataFrame(choices).replace({np.inf: np.nan, -np.inf: np.nan})
    result.to_csv(OUT / "frozen_contract_selections.csv", index=False)
    files = [OUT / "frozen_contract_selections.csv", DATA / "signal_chains.parquet"]
    manifest = {"frozen_at": datetime.now(UTC).isoformat(), "before_outcome_histories": True,
                "source_hashes": source_hashes, "selection_counts": result.selection_status.value_counts().to_dict(),
                "sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}}
    (OUT / "contract_freeze.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["selection_counts"]))


if __name__ == "__main__":
    freeze_signal_contracts()
