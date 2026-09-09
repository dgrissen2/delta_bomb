"""Acquire actual quote events for the entry-feasible, already frozen variant pairs."""

from __future__ import annotations

import argparse
import json
from datetime import date
from typing import Any

import pandas as pd

from scripts.pandar_hypothesis_quotes import OUT, Theta, verify_freeze


def request_plan(cases: pd.DataFrame, gates: pd.DataFrame) -> list[dict[str, Any]]:
    """Use entry gates only; request both fixed legs and all holding sessions."""
    feasible = set(gates.loc[gates.pass_basic.eq(True), "ticker"])
    records = []
    for case in cases.loc[cases.ticker.isin(feasible)].to_dict("records"):
        if case["selection_status"] != "selected":
            raise ValueError("entry feasible ticker has no frozen selection")
        for number in range(1, 6):
            session = case[f"holding_session_{number}"]
            if session > case["expiry"]:
                continue
            for leg in ("far", "near"):
                records.append({"ticker": case["ticker"], "signal_date": case["tradeDate"],
                                "expiry": case["expiry"], "strike": case[f"{leg}_strike"],
                                "leg": leg, "session": session})
    return records


def main(entry_audit: bool = False) -> None:
    """Each sub-minute request is one exact contract on one date, as required by Theta."""
    if entry_audit:
        plan = []
        for variant in (False, True):
            cases = verify_freeze(variant)
            for case in cases.loc[cases.selection_status.eq("selected")].to_dict("records"):
                for leg in ("far", "near"):
                    plan.append({"ticker": case["ticker"], "signal_date": case["tradeDate"],
                                 "expiry": case["expiry"], "strike": case[f"{leg}_strike"],
                                 "leg": leg, "session": case["entry_date"],
                                 "variant": "delta10_otm5" if variant else "original"})
        basename = "entry_tick"
    else:
        plan = request_plan(verify_freeze(True), pd.read_csv(OUT / "variant_entry_chain_preliminary_gates.csv"))
        basename = "tick"
    plan_path = OUT / f"{basename}_acquisition_plan.json"
    if plan_path.exists() and json.loads(plan_path.read_text())["requests"] != plan:
        raise ValueError("tick acquisition plan changed")
    if not plan_path.exists():
        plan_path.write_text(json.dumps({"basis": ("all frozen original and variant entry sessions; no profit selection"
                                                  if entry_audit else "frozen variant preliminary entry gates only; no profit selection"),
                                         "requests": plan}, indent=2) + "\n")
    client = Theta()
    manifest = []
    for record in plan:
        params = {"symbol": record["ticker"], "expiration": date.fromisoformat(record["expiry"]),
                  "strike": str(record["strike"]), "right": "call", "interval": "tick",
                  "date": date.fromisoformat(record["session"]),
                  "start_time": "09:30:00", "end_time": "16:00:00"}
        result = dict(record)
        try:
            frame, path = client.get("option_history_quote", params, "quote_event_age")
            if not frame.empty:
                if not (frame.symbol.eq(record["ticker"]).all()
                        and frame.strike.eq(record["strike"]).all()
                        and frame.right.str.lower().eq("call").all()
                        and pd.to_datetime(frame.expiration).dt.date.eq(params["expiration"]).all()
                        and pd.to_datetime(frame.timestamp).dt.date.eq(params["date"]).all()):
                    raise ValueError("quote event identity/session mismatch")
            result.update(status="ok" if len(frame) else "empty", rows=len(frame), path=path)
        except RuntimeError as exc:
            result.update(status="error", error=str(exc))
        manifest.append(result)
        (OUT / f"{basename}_history_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps({k: result[k] for k in ("ticker", "leg", "session", "status")}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry-audit", action="store_true")
    main(parser.parse_args().entry_audit)
