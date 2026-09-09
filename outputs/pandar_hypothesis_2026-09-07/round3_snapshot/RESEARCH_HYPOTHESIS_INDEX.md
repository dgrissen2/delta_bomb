# Pandar research hypothesis index

[Seed and frozen protocol](pandar_seed_and_frozen_protocol.md) · [Decision memo](memo-pndr_pandar_call_research.md) · [Native Codex provenance](../outputs/seed_expansion.json)

## Hypotheses

| Hypothesis ID | Claim | Primary Signal/Variable | Primary Target/Outcome | Scope | Note | Supporting Docs | Supporting Files | Status | Best Evidence | Next Step | Round |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H-PNDR-001 | HIRO call-flow reversal improves the initial short-call entry. | Call HIRO reversal | Net policy P&L per eligible episode: first HIRO reversal entry minus 10:01 clock entry, fixed contracts and D4 exit. | Current HIRO stocks; June descriptive pilot | [H-PNDR-001](h-pndr-001_hiro_entry_2026-09-07.md) | [Protocol](pandar_seed_and_frozen_protocol.md) | [Population](../outputs/pandar_hypothesis_2026-09-07/selected_population.csv) | inconclusive | Round 3 event replay and prior-history audit | Preserve diagnostic findings; acquire missing dated data | 3 |
| H-PNDR-002 | A next-session nearer-call purchase adds value beyond an immediate spread and covering the short at conversion. | Next-session nearer purchase | D4 net P&L differences: next-session financed conversion minus immediate spread and minus covering the original short at the same conversion timestamp. | Current HIRO stocks; June descriptive pilot | [H-PNDR-002](h-pndr-002_delayed_conversion_2026-09-07.md) | [Protocol](pandar_seed_and_frozen_protocol.md) | [Population](../outputs/pandar_hypothesis_2026-09-07/selected_population.csv) | inconclusive | Round 3 event replay and prior-history audit | Preserve diagnostic findings; acquire missing dated data | 3 |
| H-PNDR-003 | Two-session contraction in a rich call wing improves short-call profit relative to continued expansion. | Prior call-wing rollover | D4 short-only net P&L and prior-comparable bid-IV-minus-ATM normalization, rollover minus expansion at comparable starting state. | Current HIRO stocks; June descriptive pilot | [H-PNDR-003](h-pndr-003_skew_rollover_2026-09-07.md) | [Protocol](pandar_seed_and_frozen_protocol.md) | [Population](../outputs/pandar_hypothesis_2026-09-07/selected_population.csv) | inconclusive | Round 3 event replay and prior-history audit | Preserve diagnostic findings; acquire missing dated data | 3 |

## Follow-Up Experiments

| Experiment ID | Proposed Experiment | Why Run It | Scope | Parent Hypothesis | Source Note | Priority | Status |
|---|---|---|---|---|---|---|---|
| E-PNDR-001 | Audit adverse exposure before the nearer call is acquired | Converged across 1 proposer(s): charlie-mcelligott/codex. | — | H-PNDR-001 | synthesis | high | completed: event exposure ledger |
| E-PNDR-002 | Compare financed conversion with immediate purchase and same-minute short cover | Converged across 2 proposer(s): charlie-mcelligott/codex, quant/codex. | — | H-PNDR-002 | synthesis | high | completed: paired replay |
| E-PNDR-003 | Audit the frozen calls' identities and entry evidence | Converged across 1 proposer(s): quant/codex. | — | H-PNDR-001 | synthesis | high | partial: exact deliverables unavailable |
| E-PNDR-004 | Audit independent prior-history support for the two richness coordinates | Converged across 1 proposer(s): quant/codex. | — | H-PNDR-003 | synthesis | medium | completed: separate support counts |
| E-PNDR-005 | Execute the single frozen target-10-delta, minimum-5%-OTM follow-up | Converged across 2 proposer(s): charlie-mcelligott/codex, quant/codex. | — | H-PNDR-002 | synthesis | high | completed: one frozen variant |
| E-PNDR-006 | Verify event quote age and exact deliverables for preliminary variant entries | Converged across 1 proposer(s): charlie-mcelligott/codex. | — | H-PNDR-001 | synthesis | high | partial: event ages verified; deliverables unavailable |
| E-PNDR-007 | Audit policy pairing, censoring and session-counted deadlines before interpreting P&L | Converged across 1 proposer(s): quant/codex. | — | H-PNDR-001 | synthesis | high | completed: pairing and deadline audit |
| E-PNDR-008 | Verify historical deliverables for the six admitted contract pairs | Converged across 1 proposer(s): charlie-mcelligott/codex. | — | H-PNDR-001 | synthesis | high | pending dated contract metadata; continues E-PNDR-003/006 |
| E-PNDR-009 | Compare next-session financing with one frozen bullish HIRO confirmation | Converged across 1 proposer(s): charlie-mcelligott/codex. | — | H-PNDR-002 | synthesis | medium | pending complete new D1 HIRO and a separate freeze |
| E-PNDR-010 | Replicate the frozen entry and conversion controls in one later chronological block | Converged across 1 proposer(s): quant/codex. | — | H-PNDR-002 | synthesis | high | pending new chronological data block |
| E-PNDR-011 | Test the existing rollover contrast only where the later fixed sample has both states | Converged across 1 proposer(s): quant/codex. | — | H-PNDR-003 | synthesis | medium | pending both states in the same new block |
