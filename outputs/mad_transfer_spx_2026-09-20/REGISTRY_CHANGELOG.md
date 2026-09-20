

## 2026-09-20 — derive — reviewed MAD transfers and SPX disagreement

- **operator:** Codex / delta_bomb side conversation
- **operation:** additive derived experiment, no collection or source edits
- **namespace:** `/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1`
- **project:** `/Users/dgrissen/Dev/delta_bomb/outputs/mad_transfer_spx_2026-09-20`
- **inputs:** frozen eleven-sector MAD histories, completed SPXW MAD, native SPX prices and unchanged +5/−10 event outcomes
- **scope:** 2025–September18,2026; 239 dates; B09/B07/B05, strict causal above-VT only
- **calls:** ThetaData0; ORATS0; other market-data0
- **results:** OR198/318, B05F4 70/112, B07F4 14/21; all variants/policies/halves retained
- **limits:** reused dates/search history, sparse B07, overlap/date selection, policy sensitivity, informative unknowns
- **coverage:** all3141 B09 SPX endpoints available;2742 missing sector-entry slots diagnosed, no refetch or imputation
- **verification:**26654memberships;2592summaries;5093nativeVT/outcomes;10boundarytests; inherited counts and cross tables reconcile
- **dictionary_reconciled:** true; full namespace field definitions and per-file hashes/rows recorded
- **reversibility:** new namespace only; all prior raw, derived, measurement and outcome inputs unchanged
