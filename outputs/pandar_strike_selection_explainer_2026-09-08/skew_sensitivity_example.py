"""Reproduce a local Greek approximation; no forecast, acquisition, or replay.

Run from the repository root with the project's gamma_chaser Python runtime.
ORATS vega is dollars/share per one percentage point of implied volatility.
The hypothetical wing move holds ATM IV, spot, clock, and quote width unchanged.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pandas as pd


def main() -> None:
    """Save exact source inputs, local sensitivities, and the neighbor comparison."""
    root = Path(__file__).resolve().parents[2]
    output = Path(__file__).resolve().parent
    source = root / "data/pandar_hypothesis_2026-09-07/signal_chains.parquet"
    chains = pd.read_parquet(source)
    rows = chains.loc[
        chains.ticker.eq("MRVL")
        & chains.tradeDate.astype(str).str[:10].eq("2026-06-15")
        & chains.expirDate.astype(str).str[:10].eq("2026-06-26")
        & chains.strike.isin([420, 425, 430])
    ].set_index("strike")
    if not rows.index.is_unique or set(rows.index) != {420, 425, 430}:
        raise ValueError("Missing exact signal-date contracts")
    fields = [
        "ticker", "tradeDate", "expirDate", "quoteDate", "stockPrice",
        "callBidPrice", "callAskPrice", "callBidIv", "callMidIv", "callAskIv",
        "callBidSize", "callAskSize", "delta", "gamma", "vega",
    ]
    rows[fields].to_csv(output / "mrvl_sensitivity_inputs.csv")
    call = rows.loc[425]
    multiplier = 100
    width = multiplier * (call.callAskPrice - call.callBidPrice)
    fee = 2 * 0.65
    slippage = 2 * 0.01 * multiplier
    vega = multiplier * call.vega
    scenarios: list[dict[str, float]] = []
    for fall in [0, 1, 2, 3, 5]:
        gross = fall * vega
        scenarios.append({
            "wing_iv_fall_points": fall,
            "linear_short_mark_gain_dollars": gross,
            "assumed_round_trip_quote_cost_dollars": width,
            "fees_dollars": fee,
            "adverse_slippage_dollars": slippage,
            "estimated_bid_to_ask_net_dollars": gross - width - fee - slippage,
        })
    pd.DataFrame(scenarios).to_csv(output / "mrvl_skew_scenarios.csv", index=False)

    weight = math.log(425 / 420) / math.log(430 / 420)
    interp_mid = (1 - weight) * rows.loc[420].callMidIv + weight * rows.loc[430].callMidIv
    interp_ask = (1 - weight) * rows.loc[420].callAskIv + weight * rows.loc[430].callAskIv
    interp_bid = (1 - weight) * rows.loc[420].callBidIv + weight * rows.loc[430].callBidIv
    move = 0.01 * call.stockPrice
    summary = {
        "basis": "Local Greek approximation; constant spot/time/ATM/quote width except named shocks",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "provider_calls": 0,
        "new_backtest": False,
        "contract_multiplier_assumed": multiplier,
        "vega_dollars_per_vol_point": vega,
        "bid_ask_width_dollars": width,
        "break_even_wing_fall_quote_cost_only_points": width / vega,
        "break_even_wing_fall_with_fees_and_slippage_points": (width + fee + slippage) / vega,
        "one_pct_rally_delta_gamma_short_mark_loss_dollars": multiplier * (
            call.delta * move + 0.5 * call.gamma * move**2
        ),
        "neighbor_mid_iv_interpolated_pct": 100 * interp_mid,
        "target_mid_minus_neighbor_mid_points": 100 * (call.callMidIv - interp_mid),
        "target_bid_minus_neighbor_bid_points": 100 * (call.callBidIv - interp_bid),
        "target_bid_minus_neighbor_ask_points": 100 * (call.callBidIv - interp_ask),
        "long420_short425_parallel_wing_vega_dollars_per_point": multiplier * (
            rows.loc[420].vega - call.vega
        ),
        "short425_long430_parallel_wing_vega_dollars_per_point": multiplier * (
            rows.loc[430].vega - call.vega
        ),
        "limitations": [
            "Provider Greeks are model-based local sensitivities, not exact bid/ask repricing.",
            "Larger shocks need full repricing and coherent smile dynamics.",
            "An unchanged quote width is a scenario assumption, not a future liquidity forecast.",
            "Adjacent-IV interpolation is a diagnostic, not an executable arbitrage or fair-value proof.",
            "Spot shock uses frozen strike IV; changing smile dynamics can alter the result.",
            "A finite rally stress is not the maximum loss of an uncovered call.",
        ],
    }
    (output / "mrvl_skew_sensitivity.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
