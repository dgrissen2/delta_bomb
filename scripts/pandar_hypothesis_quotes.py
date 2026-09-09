"""Cache exact histories and entry chains after verifying the contract freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from scripts.pandar_hypothesis_api import DATA, ROOT, Orats, SharedBudget, ticker_batches
except ModuleNotFoundError:
    from pandar_hypothesis_api import DATA, ROOT, Orats, SharedBudget, ticker_batches

OUT = ROOT / "outputs/pandar_hypothesis_2026-09-07"


class Theta:
    """Count every explicit SDK authentication/data attempt and omit secret-bearing errors."""

    def __init__(self) -> None:
        from thetadata import ThetaClient
        self.budget = SharedBudget()
        logging.getLogger("thetadata").setLevel(logging.CRITICAL)
        attempt = self.budget.reserve("theta", "authenticate", {}, "authentication")
        try:
            self.client = ThetaClient(creds_file="/Users/dgrissen/Dev/ThetaData/creds.txt")
        except Exception as exc:
            self.budget.finish(attempt, "error", error_type=type(exc).__name__)
            raise RuntimeError(f"Theta authentication failed: {type(exc).__name__}") from None
        self.budget.finish(attempt, "ok")

    def get(self, method: str, params: dict[str, Any], phase: str) -> tuple[pd.DataFrame, str]:
        """Retain all results including empty responses; never replace a contract."""
        safe = {key: str(value) if isinstance(value, date) else value for key, value in params.items()}
        key = hashlib.sha256(json.dumps([method, safe], sort_keys=True).encode()).hexdigest()
        path = DATA / "theta" / method / f"{key}.parquet"
        if path.exists():
            return pd.read_parquet(path), str(path)
        attempt = self.budget.reserve("theta", method, safe, phase)
        try:
            result = getattr(self.client, method)(**params)
            frame = result if isinstance(result, pd.DataFrame) else result.to_pandas()
        except Exception as exc:
            code = exc.code().name if hasattr(exc, "code") else type(exc).__name__
            self.budget.finish(attempt, "error", error_type=type(exc).__name__, code=code)
            raise RuntimeError(f"Theta {method} failed: {code}") from None
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path, index=False)
        self.budget.finish(attempt, "ok", rows=len(frame), cache_path=str(path),
                           sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        return frame, str(path)


def verify_freeze(variant: bool = False) -> pd.DataFrame:
    """Refuse outcomes if an already frozen input changed."""
    freeze = json.loads((OUT / "contract_freeze.json").read_text())
    for key in ("sha256", "source_hashes"):
        for path, digest in freeze[key].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                raise ValueError(f"frozen file changed: {path}")
    hiro_path = OUT / "hiro_pre_august_decisions.parquet"
    check = {str(hiro_path): hashlib.sha256(hiro_path.read_bytes()).hexdigest(),
             str(OUT / "contract_freeze.json"): hashlib.sha256((OUT / "contract_freeze.json").read_bytes()).hexdigest()}
    audit = OUT / "before_outcome_histories.json"
    if audit.exists():
        if json.loads(audit.read_text())["hashes"] != check:
            raise ValueError("HIRO decisions or frozen contracts changed")
    else:
        audit.write_text(json.dumps({"created_at": pd.Timestamp.now(tz="UTC").isoformat(),
                                     "hashes": check}, indent=2) + "\n")
    if variant:
        variant_freeze = json.loads((OUT / "variant_freeze.json").read_text())
        for path, digest in variant_freeze["hashes"].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                raise ValueError(f"variant frozen file changed: {path}")
    return pd.read_csv(OUT / ("variant_frozen_contracts.csv" if variant else "frozen_contract_selections.csv"))


def get_histories(workers: int = 1, variant: bool = False) -> None:
    """Fetch both fixed legs across the full five-session window, with quote/Greek metadata."""
    cases = verify_freeze(variant)
    client = Theta()
    chosen = cases[cases.selection_status.eq("selected")]
    tasks = []
    for case in chosen.to_dict("records"):
        for leg in ("far", "near"):
            for kind in ("quote", "greeks_first_order"):
                tasks.append((case, leg, kind))
    manifest_path = OUT / ("variant_minute_history_manifest.json" if variant else "minute_history_manifest.json")
    # Each completed request is cached separately and the manifest is reconstructible.
    records = []

    def fetch(task: tuple[dict[str, Any], str, str]) -> dict[str, Any]:
        case, leg, kind = task
        start = case["entry_date"]
        end = min(case["expiry"], case["holding_session_5"])
        params = {"symbol": case["ticker"], "expiration": date.fromisoformat(case["expiry"]),
                  "strike": str(case[f"{leg}_strike"]), "right": "call", "interval": "1m",
                  "start_date": date.fromisoformat(start), "end_date": date.fromisoformat(end),
                  "start_time": "09:30:00", "end_time": "16:00:00"}
        record = {"ticker": case["ticker"], "signal_date": case["tradeDate"],
                  "expiry": case["expiry"], "strike": case[f"{leg}_strike"], "leg": leg,
                  "kind": kind, "start": start, "end": end}
        try:
            frame, path = client.get(f"option_history_{kind}", params, "outcome_history")
            if not frame.empty:
                assert frame.symbol.eq(case["ticker"]).all()
                assert frame.strike.eq(case[f"{leg}_strike"]).all()
                assert frame.right.str.lower().eq("call").all()
                assert pd.to_datetime(frame.expiration).dt.date.eq(date.fromisoformat(case["expiry"])).all()
                assert not frame.timestamp.duplicated().any()
            return record | {"status": "ok" if len(frame) else "empty", "rows": len(frame), "path": path}
        except RuntimeError as exc:
            return record | {"status": "error", "error": str(exc)}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch, task) for task in tasks]
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            manifest_path.write_text(json.dumps(records, indent=2) + "\n")
            print(json.dumps({key: record[key] for key in ("ticker", "leg", "kind", "status")}), flush=True)


def get_entry_chains() -> None:
    """Save the full chain and embedded underlying at the actual proposed order minute."""
    cases = verify_freeze()
    hiro = pd.read_csv(OUT / "hiro_pre_august_candidates.csv")
    client = Orats()
    records, chains = [], []
    for case in cases[cases.selection_status.eq("selected")].to_dict("records"):
        times = {"clock": f"{case['entry_date']} 10:01:00"}
        match = hiro[hiro.ticker.eq(case["ticker"]) & hiro.tradeDate.eq(case["tradeDate"])]
        if len(match) == 1 and pd.notna(match.iloc[0].first_action_at):
            if pd.notna(match.iloc[0].first_trigger_history_complete) and bool(match.iloc[0].first_trigger_history_complete):
                times["hiro"] = match.iloc[0].first_action_at
        for policy, timestamp in times.items():
            stamp = pd.Timestamp(timestamp)
            params = {"ticker": case["ticker"], "tradeDate": stamp.strftime("%Y%m%d%H%M")}
            try:
                rows = client.get("historical/one-minute/strikes/chain", params, "actual_entry_chain")
                chains.extend(dict(row, entry_policy=policy, signal_date=case["tradeDate"],
                                   requested_at=str(stamp)) for row in rows)
                records.append({"ticker": case["ticker"], "policy": policy, "timestamp": str(stamp),
                                "status": "ok" if rows else "empty", "rows": len(rows)})
            except RuntimeError as exc:
                records.append({"ticker": case["ticker"], "policy": policy, "timestamp": str(stamp),
                                "status": "error", "error": str(exc)})
            print(json.dumps(records[-1]), flush=True)
    pd.DataFrame(chains).to_parquet(DATA / "actual_entry_chains.parquet", index=False)
    (OUT / "entry_chain_manifest.json").write_text(json.dumps(records, indent=2) + "\n")


def get_theta_entries() -> None:
    """Collect dated listings and all-call Greeks in the selected expiry at actual entries."""
    cases = verify_freeze()
    chosen = cases[cases.selection_status.eq("selected")]
    hiro = pd.read_csv(OUT / "hiro_pre_august_candidates.csv")
    client = Theta()
    records = []
    for signal, group in chosen.groupby("tradeDate"):
        for batch in ticker_batches(group.ticker.tolist()):
            params = {"request_type": "quote", "date": date.fromisoformat(signal),
                      "symbol": batch, "max_dte": 35}
            try:
                frame, path = client.get("option_list_contracts", params, "signal_contract_listing")
                records.append({"kind": "listing", "signal_date": signal, "tickers": batch,
                                "status": "ok", "rows": len(frame), "path": path})
            except RuntimeError as exc:
                records.append({"kind": "listing", "signal_date": signal, "tickers": batch,
                                "status": "error", "error": str(exc)})
    for case in chosen.to_dict("records"):
        times = {"clock": f"{case['entry_date']} 10:01:00"}
        match = hiro[hiro.ticker.eq(case["ticker"]) & hiro.tradeDate.eq(case["tradeDate"])]
        if len(match) == 1 and pd.notna(match.iloc[0].first_action_at):
            if pd.notna(match.iloc[0].first_trigger_history_complete) and bool(match.iloc[0].first_trigger_history_complete):
                times["hiro"] = match.iloc[0].first_action_at
        for policy, stamp_string in times.items():
            stamp = pd.Timestamp(stamp_string)
            params = {"symbol": case["ticker"], "expiration": date.fromisoformat(case["expiry"]),
                      "strike": "*", "right": "call", "date": stamp.date(), "interval": "1m",
                      "start_time": stamp.strftime("%H:%M:%S"), "end_time": stamp.strftime("%H:%M:%S")}
            record = {"kind": "entry_chain", "ticker": case["ticker"], "signal_date": case["tradeDate"],
                      "policy": policy, "timestamp": stamp_string, "expiry": case["expiry"]}
            try:
                frame, path = client.get("option_history_greeks_first_order", params, "actual_entry_chain")
                record.update(status="ok" if len(frame) else "empty", rows=len(frame), path=path)
            except RuntimeError as exc:
                record.update(status="error", error=str(exc))
            records.append(record)
            (OUT / "theta_entry_manifest.json").write_text(json.dumps(records, indent=2) + "\n")
            print(json.dumps({k: record[k] for k in ("ticker", "policy", "status")}), flush=True)


def get_entry_quotes() -> None:
    """Retrieve the whole selected-expiry quote snapshot, reusing it across frozen arms."""
    verify_freeze(True)
    client = Theta()
    entries = json.loads((OUT / "theta_entry_manifest.json").read_text())
    records = []
    for entry in entries:
        if entry["kind"] != "entry_chain":
            continue
        stamp = pd.Timestamp(entry["timestamp"])
        params = {"symbol": entry["ticker"], "expiration": date.fromisoformat(entry["expiry"]),
                  "strike": "*", "right": "call", "date": stamp.date(), "interval": "1m",
                  "start_time": stamp.strftime("%H:%M:%S"), "end_time": stamp.strftime("%H:%M:%S")}
        record = {k: entry[k] for k in ("ticker", "signal_date", "policy", "timestamp", "expiry")}
        try:
            frame, path = client.get("option_history_quote", params, "actual_entry_quote_chain")
            record.update(status="ok" if len(frame) else "empty", rows=len(frame), path=path)
        except RuntimeError as exc:
            record.update(status="error", error=str(exc))
        records.append(record)
        (OUT / "entry_quote_manifest.json").write_text(json.dumps(records, indent=2) + "\n")
        print(json.dumps({k: record[k] for k in ("ticker", "policy", "status")}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", action="store_true")
    parser.add_argument("--histories", action="store_true")
    parser.add_argument("--theta-entries", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--variant", action="store_true")
    parser.add_argument("--entry-quotes", action="store_true")
    args = parser.parse_args()
    if args.entries:
        get_entry_chains()
    if args.histories:
        get_histories(args.workers, args.variant)
    if args.theta_entries:
        get_theta_entries()
    if args.entry_quotes:
        get_entry_quotes()
