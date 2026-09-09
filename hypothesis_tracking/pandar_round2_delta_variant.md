# Round 2: one higher-delta feasibility variant

The [original frozen specification](pandar_seed_and_frozen_protocol.md) remains unchanged. On its 49 selected pairs, 83 available clock/HIRO entry snapshots failed at least one of the original bid, delta, distance or relative-spread gates. No option P&L was used to select this follow-up. Charlie and Quant each recommended exactly one higher-delta arm in response to that entry-feasibility result and the user's request to relax delta and combine it with OTM distance.

Use the same frozen 50-episode population and signal chains. Choose the original nearest-ten-day expiry inside 7–14 calendar DTE. Select an OTM call with **delta 0.05–0.15 inclusive, nearest 0.10, at least 5% above spot**; lower strike breaks a delta-distance tie. The nearer call remains the immediately adjacent lower listed call in the same expiry, still OTM. Do not try another expiry if this one has no qualifying pair. Recheck the same far-call delta band and 5% OTM floor at actual entry. Keep every original quote, spread, displayed-size, timing, earnings, fee and closing rule.

This is a project research variant, not an assertion about Pandar's delta requirements or an optimal band. It raises directional exposure. Five percent OTM does not equalize expected-move distance across stocks; report both coordinates and short-phase exposure.

Freeze every pair before requesting additional outcome histories. Some variant legs may overlap original contracts whose raw histories were already acquired; flag those explicitly. The variant is an exploratory follow-up prompted by entry evidence, not a pristine untouched holdout or a claim that all of its raw prices were unavailable beforehand. Neither agent nor root selected it by inspecting profit paths.

Acquire comparable prior history for cases that can pass the observed initial-entry gates, using only those causal gate observations to allocate the shared 2,000-call budget. Failed original/variant entries remain in the population and carry explicit uncollected-history reasons; they cannot count as successful richness measurements. No thresholds will be changed again within this variant after its profit paths are evaluated.

Backlinks: [index](RESEARCH_HYPOTHESIS_INDEX.md), [conversion claim](h-pndr-002_delayed_conversion_2026-09-07.md), [entry gate observations](../outputs/pandar_hypothesis_2026-09-07/entry_chain_preliminary_gates.csv), [source contract freeze](../outputs/pandar_hypothesis_2026-09-07/contract_freeze.json).
