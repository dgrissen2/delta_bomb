"""Render the complete frozen research sample and paired trade diagnostics for review."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "outputs/pandar_hypothesis_2026-09-07"


def money(value: object) -> str:
    if pd.isna(value):
        return "unavailable"
    number = float(value)
    return f"−${abs(number):,.2f}" if number < 0 else f"${number:,.2f}"


def time(value: object) -> str:
    return "none" if pd.isna(value) else pd.Timestamp(value).strftime("%m-%d %H:%M")


def main() -> None:
    table = pd.read_csv(OUT / "event_policy_replay.csv")
    cases = pd.read_csv(OUT / "event_admitted_case_comparisons.csv")
    summary = json.loads((OUT / "event_replay_summary.json").read_text())
    budget = json.loads((OUT / "api_budget.json").read_text())
    selected = table[table.slippage_per_share.eq(.01) & table.initial_status.eq("entered")]
    text = """# Pandar call sales: frozen June sample and leg timing

The wider delta experiment found additional call-sale candidates. The original project selection targeted 5 delta inside a 2–10 band and produced no admitted sales; the one exploratory follow-up targets 10 delta inside 5–15, requires at least 5% OTM, and preserves the expiry, liquidity, cost and timing rules. **Neither band—including the earlier 2–6 choice—came from Pandar.** These are research assumptions, not a claim about his preferred strikes.

This is a historical quoted-price study. Dollar figures assume a 100-share contract. Actual NBBO event times, sizes and conditions are checked, but exact historical deliverables remain unverified; these are not actual fills or certified executable trades. The [interpretation guide](../../hypothesis_tracking/pandar_replay_interpretation.md) explains unavailable results, no-purchase paths and zero-bid marks.

The clearest findings are:

- **MRVL's June 16 clock sale made $168.70 by D4 if the original short was retained.** Buying the nearer call the next session made $46.40. Both are profitable, but the purchase consumed much of the short sale's profit.
- **ORCL's second-session conversion made $55.40 by D4, versus −$13.30 for covering at that purchase minute.** The far call had a very wide $0.03/$0.94 quote while the nearer call could be bought at $0.18. This is evidence about relative closing liquidity; it does not establish a forecast of a rebound. Retaining the short to D4 made $72.70.
- **QCOM's next-session conversion made $9.40 by D4**, versus −$11.30 for covering at purchase and −$20.30 for keeping the original short to D4. The same conversion lost $29.60 at D5. The preselected closing deadline matters.
- Buying the spread immediately lost in every priced admitted example. All 14 completed deferred purchases beat that comparator at D4, but most still lost to covering the original short at purchase. There is no general instruction here to buy a second leg merely because the first premium finances it.

## The full candidate population

The [50-stock eligibility and strike tables](eligibility_and_richness_tables.md) show every signal date, entry session, qualification reason, IV/RR ranks, skew age/depth, IV versus RV, and both fixed contract selections. The [combined CSV](eligibility_and_richness_tables.csv) is the machine-readable version. The [41,864-row population ledger](population_ledger.csv) preserves failed selection reasons.

Only current HIRO stock tickers were used. Historical actual earnings on the signal/order day through the next 30 calendar days were excluded, as authorized. ORATS supplied 26,510 valid events for 315 of 323 stocks; eight names remain without event coverage and nine invalid date placeholders were quarantined. This repairs the retrospective earnings gate, not historical knowledge of the schedule.

Fifty nonoverlapping episodes remain across June 12, 15, 16, 17 and 18, 2026. Available stock HIRO archives extend the test before August but do not provide an earlier continuous stock history: the [coverage audit](data_readiness.md) documents the archive search and observed short retention. Current membership applied backward is also a limitation. There is no independent later holdout in this five-date pilot.

## Every admitted sale, with the same closing deadline

“Buy D0/D1/D2” means the first qualifying purchase of the fixed nearer call in that sale session / next trading session / second trading session. The original short sale is shared across all columns in each row. A failed purchase keeps the short until the common exit; a missing path stays unavailable. The immediate-spread comparator buys the nearer call with the sale. Short-only covers the far call at the final deadline.

All figures below include $0.65 per action and $0.01 per share adverse slippage. D4 closes at 15:50 ET in holding session four, counting the sale as session one. D5 is the separately specified secondary deadline. Expiry caps either deadline. **A positive result does not mean that buying the nearer call improved the original sale.**
"""
    text += "\n### What the calls looked like at the actual sale\n\nIV/RR ranks below belong to the signal date; delta, distance, spot and NBBO event age are rechecked at the order. These ranks are descriptive and were not additional admission thresholds.\n\n| Stock / policy | Sale ET | Spot | Far delta points | Far OTM % | Bid / ask | Quote age seconds | Signal IV30 rank | Signal RR30 rank |\n|---|---|---:|---:|---:|---|---:|---:|---:|\n"
    features = pd.read_csv(OUT / "eligibility_features.csv").set_index(["ticker", "signal_date"])
    for row in selected[selected.holding_sessions.eq(4) & selected.method.eq("short_only")].to_dict("records"):
        feature = features.loc[(row["ticker"], row["signal_date"])]
        observation = json.loads(row["entry_quote_observations"])["far"]
        text += f"| {row['ticker']} / {row['entry_policy']} | {time(row['entry_at'])} | {observation['underlying_price']:.2f} | {100*row['entry_far_delta']:.2f} | {row['entry_far_otm_pct']:.2f} | {money(row['entry_far_bid'])} / {money(row['entry_far_ask'])} | {observation['quote_age_seconds']:.3f} | {feature.iv30_rank_pct:.1f} | {feature.rr30_rank_pct:.1f} |\n"
    for horizon in (4, 5):
        text += f"\n### Holding session {horizon}\n\n| Stock / sale policy | Sale time ET | Expiry; short / long strikes | Initial bid | Immediate spread | Buy D0 | Buy D1 | Buy D2 | Short-only |\n|---|---|---|---:|---:|---:|---:|---:|---:|\n"
        for row in cases[cases.holding_sessions.eq(horizon)].to_dict("records"):
            values = []
            for method in ("immediate_spread", "deferred_d0", "deferred_d1", "deferred_d2", "short_only"):
                value = money(row.get(f"{method}_pnl_net"))
                if row.get(f"{method}_completion_status") == "known_no_purchase":
                    value += " · no purchase; short retained"
                if row.get(f"{method}_exit_status") == "zero_bid_long_mark":
                    value += " · zero-bid long mark"
                values.append(value)
            text += f"| {row['ticker']} / {row['entry_policy']} | {time(row['entry_at'])} | {row['expiry']}; {row['far_strike']:g} / {row['near_strike']:g} | {money(row['entry_far_bid'])} | " + " | ".join(values) + " |\n"
    text += """
Zero-bid long marks, missing exits and all arm statuses are retained in the [detailed comparison CSV](event_admitted_case_comparisons.csv). A stale closing quote does not support the fixed closing price, even if the minute-only view looks profitable. The [minute-only comparison](admitted_case_comparisons.csv) remains a separate sensitivity, not a replacement for the event-age result.

## When the second call was actually purchased

The table includes all D4 completed deferred purchases, including losses. “Cover instead” covers the original short at that exact purchase minute and holds cash until the same final deadline. “Added by purchase” is final spread P&L minus that cash result. Prices are per share before the separately charged fees/slippage; dollars are per assumed standard contract.

| Stock / sale policy | Purchase window | Near strike | Purchase time ET | Ask | Delta points | OTM % | Final P&L | Cover instead | Added by purchase |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
"""
    purchases = selected[selected.holding_sessions.eq(4) & selected.method.str.startswith("deferred")
                         & selected.completion_status.eq("completed")]
    for r in purchases.sort_values(["ticker", "entry_policy", "method"]).to_dict("records"):
        text += f"| {r['ticker']} / {r['entry_policy']} | {r['method'].replace('deferred_', '').upper()} | {r['near_strike']:g} | {time(r['conversion_at'])} | {money(r['purchase_ask'])} | {r['purchase_delta']*100:.2f} | {r['purchase_otm_pct']:.2f} | {money(r['pnl_net'])} | {money(r['cover_at_conversion_pnl'])} | {money(r['incremental_vs_conversion_cover'])} |\n"
    text += """
The later purchase rule uses price financing, OTM status, Greeks, earnings and quote quality. **HIRO times the initial sale only; the second purchase has no later HIRO confirmation in this specification.** A bullish flow/rebound trigger would be another experiment, requiring adequate later-session HIRO data and another pre-outcome freeze.

The [second-leg HIRO coverage audit](second_leg_hiro_coverage.md) makes that limitation concrete. Only PLTR and ORCL have D1 archives among the six admitted stocks; ORCL has an opening gap. Only PLTR has D2 coverage. The available files therefore cannot supply a complete six-name test of a later flow trigger. Two selected case studies would not repair that missing denominator.

## Richness and the skew journey

The six measured calls are PLTR, DIS, MRVL, ORCL, QCOM and CRM. [Their prior richness table](eligibility_and_richness_tables.md) reports each coordinate separately. MRVL is at the 99.1st comparable-delta/DTE percentile, but its comparable forward-moneyness history has only 30 valid dates. QCOM has only 38 in that second coordinate. Both remain unavailable there under the 60-observation minimum. CRM is near the 96th percentile in both supported coordinates. DIS has a negative absolute bid-IV-minus-ATM spread despite an elevated historical percentile.

These scores use strictly prior comparable surfaces, not the lifetime of a newly listed weekly contract. They match delta/DTE and, separately, forward-moneyness/DTE; supported interpolation stays inside smiles. The ATM reference uses an ORATS carry-model forward checked against ORATS model put/call values, not an independently observed forward. Prior histories include earnings periods. The [full observations](strike_richness_history.json) preserve unavailable dates and support counts.

The [Charlie feature read](charlie_round3_feature_read.md) explains the distinctions. All six measured names are age one or two in the high-wing episode; none has the frozen two-session rollover pattern. Only one of the full 50, CPNG, is a rollover case. Thus this sample cannot test whether mature, contracting call skew beats continued expansion. Only DIS among the six has both 30/60-day implied variance above trailing realized variance. No extra filter was selected from these profits.

## Exposure, missing cases and statistical limits

The [complete 4,000-row event replay](event_policy_replay.csv) retains two 50-case populations, two sale policies, five purchase methods, two deadlines and two fixed-time cost assumptions. Rejected and unavailable entries are preserved, as are every rejected purchase minute and its observed gate inputs. The [paired summary](event_replay_summary.json) reports each comparison's coverage rather than silently dropping missing paths.
"""
    for variant in ("original", "delta10_otm5"):
        sample = table[table.variant.eq(variant)].drop_duplicates(["ticker", "entry_policy"])
        counts = sample.initial_status.value_counts().to_dict()
        text += f"\n- {variant}: {counts.get('entered', 0)} admitted sale-policy cases, {counts.get('known_no_entry', 0)} known skipped sales and {counts.get('censored_entry', 0)} unavailable entries, out of 100 stock/policy slots.\n"
    text += """
The [short-phase event exposure ledger](tick_short_phase_exposure.csv) measures adverse short-cover quotes before the nearer call is acquired, including intraminute events. Minute data also retain peak observed delta and underlying rallies. These are observed historical paths, not maximum-loss bounds; overnight gaps, missing data and early assignment are not simulated. Naked-phase minutes include calendar time where labeled. An unavailable conversion path is labeled a hypothetical unconverted scenario, not a measured actual phase duration.

Opening quotes are a material exposure caveat: before the next-session purchases, MRVL's clock path reached an observed $279.30 cover loss, CRM $220.30, and ORCL $919.30. ORCL's extreme was a fresh but one-sided $0 bid / $10 ask. The replay deliberately does not impose the opening-entry width limit on a forced-cover mark. These are adverse displayed asks, not proof of traded losses or a typical slippage forecast; their exact times are retained in the ledger.

The fixed five-session date block contains this entire sample. The [2,000 actual block resamples](block_resampling.json) preserve cross-sectional episodes and are degenerate: there is no independent interval or statistical pass. The minimum was 20 distinct entry dates, and we have five. Attractive individual examples can explain the cash flows but cannot establish a dependable trading rule.

## Data and reproduction

The original/variant populations, signal chains and selection hashes were saved before their outcomes. The higher-delta arm was chosen from original entry failures; eleven legs overlap previously acquired raw original histories, so the variant is explicitly exploratory. The initial ORATS intraday fallback incorrectly repeated 83 forbidden requests before the persistent circuit breaker was added; all attempts remain charged. Theta supplied the historical quotes and Greeks. See [budget](api_budget.json), [contract audit](contract_reference_audit.md), [original freeze](contract_freeze.json), [variant freeze](variant_freeze.json), and [hypothesis memo](../../hypothesis_tracking/memo-pndr_pandar_call_research.md).

All 98 original selected legs and 94 variant selected legs also match exact tuples in the signal-date Theta quote-contract listings. The [listing reconciliation](signal_listing_reconciliation.csv) retains each match and source. This establishes historical quote-list presence, not the missing dated deliverable terms.
"""
    text += f"\nProvider attempts used: **{budget['used']:,} / {budget['limit']:,}**. Supported ORATS endpoints were batched up to ten names. Tick quotes require one exact contract/session per request; cached overlaps were reused. The split endpoint's failed batching probe is retained and its relevant names were fetched individually. No orders were placed.\n"
    text += "\nReproduce with `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -m scripts.pandar_hypothesis_event_replay`, then `-m scripts.pandar_hypothesis_event_exposure`, the resampling command recorded in its artifact, and `-m scripts.pandar_hypothesis_report`. Input source hashes are saved in the replay summaries.\n"
    (OUT / "pandar_trade_results.md").write_text(text)
    assert summary["rows"] == len(table) == 4000


if __name__ == "__main__":
    main()
