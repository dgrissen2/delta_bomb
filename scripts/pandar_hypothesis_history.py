"""Acquire and measure prior comparable smiles for causally feasible frozen entries."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

try:
    from scripts.pandar_hypothesis_api import DATA, ROOT, Orats, ticker_batches
    from scripts.pandar_hypothesis_richness import evaluate_richness
except ModuleNotFoundError:
    from pandar_hypothesis_api import DATA, ROOT, Orats, ticker_batches
    from pandar_hypothesis_richness import evaluate_richness

OUT = ROOT / "outputs/pandar_hypothesis_2026-09-07"


def acquisition_plan() -> dict[str, Any]:
    """Allocate history by entry-time quote feasibility, never by profits or later paths."""
    path = OUT / "richness_acquisition_plan.json"
    if path.exists():
        return json.loads(path.read_text())
    gates = pd.read_csv(OUT / "variant_entry_chain_preliminary_gates.csv")
    tickers = sorted(gates.loc[gates.pass_basic.eq(True), "ticker"].unique())
    cases = pd.read_csv(OUT / "variant_frozen_contracts.csv")
    cases = cases[cases.ticker.isin(tickers)]
    calendar = pd.read_parquet(ROOT / "docs/replay/pandar_skew_journey_2026-09-06/daily_features_and_outcomes.parquet",
                               columns=["tradeDate"])
    sessions = sorted(pd.to_datetime(calendar.tradeDate).dt.strftime("%Y-%m-%d").unique())
    by_date: dict[str, list[str]] = defaultdict(list)
    current: dict[str, list[str]] = defaultdict(list)
    for row in cases.itertuples():
        current[row.tradeDate].append(row.ticker)
        for day in [s for s in sessions if s < row.tradeDate][-126:]:
            by_date[day].append(row.ticker)
    tasks = []
    for day, names in sorted(by_date.items()):
        for batch in ticker_batches(names):
            for endpoint in ("hist/strikes", "hist/monies/implied"):
                params = {"ticker": ",".join(batch), "tradeDate": day}
                if endpoint == "hist/strikes":
                    params["dte"] = "1,35"
                tasks.append({"endpoint": endpoint, "params": params, "role": "prior"})
    for day, names in sorted(current.items()):
        for batch in ticker_batches(names):
            tasks.append({"endpoint": "hist/monies/implied",
                          "params": {"ticker": ",".join(batch), "tradeDate": day}, "role": "signal"})
    plan = {"created_at": pd.Timestamp.now(tz="UTC").isoformat(), "tickers": tickers,
            "basis": "Frozen variant entry-price/delta gates only; no outcome/P&L selection",
            "source_gate_sha256": hashlib.sha256((OUT / "variant_entry_chain_preliminary_gates.csv").read_bytes()).hexdigest(),
            "sessions": sessions, "tasks": tasks, "expected_uncached_calls_upper_bound": len(tasks)}
    path.write_text(json.dumps(plan, indent=2) + "\n")
    return plan


def fetch() -> None:
    """Fetch ten-name-or-smaller daily batches; preserve each raw success/failure."""
    plan = acquisition_plan()
    client = Orats()
    records = []
    frames: dict[str, list[pd.DataFrame]] = defaultdict(list)
    for i, task in enumerate(plan["tasks"], 1):
        started = time.monotonic()
        try:
            rows = client.get(task["endpoint"], task["params"], "prior_comparable_history")
            frame = pd.DataFrame(rows)
            if len(frame):
                frames[task["endpoint"]].append(frame)
            record = task | {"status": "ok" if rows else "empty", "rows": len(rows)}
        except RuntimeError as exc:
            record = task | {"status": "error", "error": str(exc)}
        records.append(record)
        (OUT / "richness_history_fetch_manifest.json").write_text(json.dumps(records, indent=2) + "\n")
        if i % 10 == 0 or i == len(plan["tasks"]):
            print(json.dumps({"completed": i, "total": len(plan["tasks"]),
                              "last_date": task["params"]["tradeDate"], "status": record["status"]}), flush=True)
        time.sleep(max(0, .55 - (time.monotonic() - started)))
    for endpoint, items in frames.items():
        pd.concat(items, ignore_index=True).to_parquet(DATA / f"richness_{endpoint.replace('/', '_')}.parquet",
                                                      index=False)


def build_forwards(monies: pd.DataFrame, strikes: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Carry-model forwards with explicit near-ATM parity diagnostics, not spot substitution."""
    forwards, rows = {}, []
    chain_groups = {(t, str(day)[:10], str(exp)[:10]): group for (t, day, exp), group
                    in strikes.groupby(["ticker", "tradeDate", "expirDate"])}
    for row in monies.to_dict("records"):
        key = (row["ticker"], str(row["tradeDate"])[:10], str(row["expirDate"])[:10])
        t = (pd.Timestamp(key[2]) - pd.Timestamp(key[1])).days / 365
        item = dict(ticker=key[0], tradeDate=key[1], expiry=key[2], status="missing_carry_inputs")
        if str(row.get("quoteDate", ""))[:10] != key[1]:
            rows.append(item | {"status": "carry_quote_date_unavailable_or_stale"})
            continue
        fields = [row.get(k) for k in ("stockPrice", "riskFreeRate", "yieldRate", "residualYieldRate")]
        if t > 0 and all(v is not None and np.isfinite(float(v)) for v in fields):
            spot, rate, yield_rate, residual = map(float, fields)
            forward = spot * math.exp((rate - yield_rate - residual) * t)
            item.update(spot=spot, risk_free_rate=rate, dividend_yield=yield_rate,
                        residual_yield=residual, calendar_time_years=t, carry_forward=forward,
                        status="missing_parity_support")
            chain = chain_groups.get(key)
            if chain is not None:
                near = chain[chain.delta.between(.35, .65)].copy()
                if "quoteDate" not in near:
                    near = near.iloc[:0]
                else:
                    near = near[near.quoteDate.astype(str).str[:10].eq(key[1])]
                # Repeated copies cannot create support; conflicting quotes at a strike are unusable.
                near = near.drop_duplicates()
                near = near[~near.strike.duplicated(keep=False)]
                if {"callValue", "putValue"} <= set(near):
                    parity = near.strike + math.exp(rate * t) * (near.callValue - near.putValue)
                    parity = parity[np.isfinite(parity)]
                    if len(parity) >= 2 and spot > 0 and forward > 0:
                        parity_median = float(parity.median())
                        deviation = abs(parity_median - forward) / spot
                        item.update(parity_forward_median=parity_median,
                                    parity_points=len(parity), parity_deviation_spot_fraction=deviation,
                                    status="model_carry_parity_consistent" if deviation <= .01 else "carry_parity_disagreement")
                        if deviation <= .01:
                            forwards[key] = forward
        rows.append(item)
    return forwards, pd.DataFrame(rows)


def calculate() -> None:
    """Keep separate supported history counts and unavailable rows for every frozen pair."""
    plan = acquisition_plan()
    strikes = pd.read_parquet(DATA / "richness_hist_strikes.parquet")
    signal = pd.read_parquet(DATA / "signal_chains.parquet")
    monies = pd.read_parquet(DATA / "richness_hist_monies_implied.parquet")
    all_strikes = pd.concat([strikes, signal[signal.ticker.isin(plan["tickers"])]], ignore_index=True)
    all_strikes = all_strikes.drop_duplicates(["ticker", "tradeDate", "expirDate", "strike"])
    forwards, forward_audit = build_forwards(monies, all_strikes)
    forward_audit.to_csv(OUT / "forward_coordinate_audit.csv", index=False)
    cases = pd.read_csv(OUT / "variant_frozen_contracts.csv")
    detailed, flat = [], []
    for case in cases.to_dict("records"):
        basic = {"ticker": case["ticker"], "signal_date": case["tradeDate"],
                 "expiry": case["expiry"], "strike": case.get("far_strike"), "variant": "delta10_otm5"}
        if case["ticker"] not in plan["tickers"]:
            flat.append(basic | {"status": "history_not_requested_no_preliminary_entry"})
            continue
        current = signal[(signal.ticker == case["ticker"]) & (signal.tradeDate == case["tradeDate"])].to_dict("records")
        hist = {str(day)[:10]: group.to_dict("records") for day, group in
                strikes[strikes.ticker.eq(case["ticker"])].groupby("tradeDate")}
        fmap = {(day, exp): value for (ticker, day, exp), value in forwards.items() if ticker == case["ticker"]}
        result = evaluate_richness(current, hist, signal_date=case["tradeDate"], expiry=case["expiry"],
                                   strike=case["far_strike"], session_dates=plan["sessions"], forwards=fmap)
        result["forward_type"] = "ORATS_carry_model_estimate_internally_model_consistent_not_observed"
        result["atm_definition"] = "call_mid_iv_at_carry_model_forward_not_independently_verified"
        detailed.append(result)
        record = basic | {"status": result["current"]["status"], **result["current"],
                          "forward_type": result["forward_type"], "atm_definition": result["atm_definition"]}
        for mode, block in result["coordinates"].items():
            record.update({f"{mode}_{key}": block[key] for key in
                           ("n", "mean", "sample_std", "z", "midrank_percentile", "status")})
        flat.append(record)
    (OUT / "strike_richness_history.json").write_text(json.dumps(detailed, indent=2) + "\n")
    pd.DataFrame(flat).to_csv(OUT / "strike_richness.csv", index=False)
    print(pd.DataFrame(flat).loc[lambda x: x.ticker.isin(plan["tickers"])].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--calculate", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        fetch()
    if args.calculate:
        calculate()
