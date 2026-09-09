# Charlie and Brent: research decisions

These were independent persona simulations within this Codex task. The actual people
were not contacted. Canonical sources:

- [Charlie McElligott](/Users/dgrissen/.config/skillshare/personas/market/charlie-mcelligott.md)
- [Brent Kochuba](/Users/dgrissen/.config/skillshare/personas/strategy/brent-kochuba.md)

The agents received bounded context and returned structured reviews. Neither explored
additional market data. A separate panel arbitrator read only their initial outputs.

## Before outcomes

```json
{
  "charlie": {
    "decision": "Test flow exhaustion with next-quote execution; compare clock and financing rules.",
    "key_points": ["Prior-EOD qualification", "Deduplicate contracts", "Retain failed legs", "Separate short-call profit from conversion value"],
    "risks": ["Bid/ask friction", "Single-name dependence", "Hindsight timestamps"],
    "confidence": "low"
  },
  "brent": {
    "decision": "Buy put inventory in calm put-selling flow; complete after downside demand plus an executable price target.",
    "key_points": ["Put HIRO positive means put selling", "Observe first, execute later", "Close uncompleted long at deadline"],
    "risks": ["Naked call phase", "Missing historical gamma terrain", "Profitable outcomes do not validate mechanics"],
    "confidence": "low"
  },
  "arbitrator": {
    "decision": "Use Brent's calm put entry as primary; keep entries fixed while comparing price-only, HIRO-plus-price, and clock completions.",
    "rationale": "Preserves the cheap-inventory mechanism and avoids searching alternative momentum entries.",
    "tradeoffs": ["Continue requested retrospective naked-call audit", "No deployment approval inferred", "Keep failed and censored observations"]
  }
}
```

## After outcomes

```json
{
  "charlie": {
    "decision": "Delayed call conversion produced two profitable examples; no conversion alpha or HIRO timing edge established.",
    "key_points": ["Premium contraction generated the first-leg profit", "Conversion spent part of that profit", "Price targets determine affordability", "No successful financed put spread in observed windows"],
    "risks": ["Two correlated MSTR episodes", "Tiny profits sensitive to friction", "Clock and HIRO cohorts must be paired"],
    "confidence": "high on arithmetic, low on repeatability"
  },
  "brent": {
    "decision": "Accept the cases as modeled retrospective evidence; veto deployment of the naked-short phase.",
    "key_points": ["Delayed premium purchase helped", "Conversion underperformed covering at that moment", "Short put test cannot reject longer-life tail insurance"],
    "risks": ["Sampled losses do not cap gap risk", "No gamma-terrain validation", "Negative spread liquidation quotes reflect friction, not contractual payoff risk"],
    "confidence": "high on evidence boundaries, low on deployment"
  }
}
```

Final synthesis: preserve the next-day and two-day profitable call examples, including
the same-day price-financed alternative. Show closing the first short as a baseline.
Do not promote an optimal waiting period or HIRO edge from two episodes. Keep the put
program as inventory research; this replay did not show fast financed conversions.

Two precision corrections to the initial result packet are incorporated in the report:
fixed +1 beat HIRO only in the 155/160 case (not the 145/150 case); and only 18 of 27
distinct put entries have a complete two-session financing horizon, with nine censored.
There is no material final disagreement requiring further arbitration: Brent's deployment
veto and Charlie's retrospective interpretation concern different decisions.

## Source dime-target addendum

Charlie separately reviewed the source-rule sensitivity after the primary results:

```json
{
  "assessment": "Fair original-target examples when labelled as a separately evaluated sensitivity with unchanged entries and deadlines.",
  "finding": "Price-only dime completion earned $10.40/$11.40. HIRO delayed both to +2 sessions, earning $10.40/$22.40.",
  "limits": ["No HIRO dime completions by +1", "Two days is not established as optimal", "Case B beat covering at conversion by only $0.70", "That advantage disappears with one-cent slippage on two extra transactions"],
  "decision": "Keep the source-target examples alongside the frozen fee-covering results; describe the subsequent rally as an observed outcome, not a validated timing mechanism."
}
```

## September 6: missed calls and the delta boundary

Charlie and Brent independently reviewed the selection omission and broader discovery
proposal through the same canonical global personas. These remain persona simulations.
Their review preceded the broader outcome analysis; no subsequent P&L was used.

**Charlie:** Fix selection separately from changing the delta band. Enumerate every
quote-qualified 2–10Δ call, report 5–12 and 13–19 DTE separately, and preserve the
2–6 benchmark. Compare bid IV with ATM and comparable-delta deferred IV. Record delta
and % OTM independently; low delta does not define distance to the strike. Retain
failed and missing observations, and deduplicate/cluster repeated ticker exposures
before evaluating outcomes. Sizing comparisons need strike-touch stress budgets.

**Brent:** Treat front-wing rank ≥85 as a discovery proxy, with all removed project
surface vetoes visible. Check actual sale-side richness across expirations and the
associated event estimates. An EOD quote is not a fill, and HIRO cannot establish
option richness or dealer gamma. Replay the recovered unchanged-rule selections
first, then the separately labelled wider research population.

**Synthesis:** There is no material disagreement. The selector is corrected, 2–10Δ
is an explicit research override, and the 413-stock-day search retains all exclusions.
The audit finds 73 selected quote-qualified stock-days at 2–10Δ, with 33 passing both
current bid-richness diagnostics. These counts do not demonstrate profitability or
replace the exact-strike historical z-score work. The original timing cohort remains
frozen; new selections still need prospective-sequence HIRO/minute-quote replay.
