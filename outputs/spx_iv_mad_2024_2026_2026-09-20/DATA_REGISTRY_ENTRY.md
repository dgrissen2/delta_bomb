

## 2026-09-20 — backfill — SPX IV acceleration MAD history from 2024

- **date:** 2026-09-20
- **operator:** Codex / delta_bomb SPX MAD continuation
- **repo_session:** delta_bomb
- **op_type:** backfill
- **paths_touched:** `/Users/dgrissen/Dev/central_trade_data/thetadata/spx_iv_mad_2024_2026_2026-09-20-v1/`; `/Users/dgrissen/Dev/central_trade_data/DATA_DICTIONARY.md`
- **size_delta_bytes:** +2197682952 (payload excluding namespace inventory/dictionary and root registry markdown)
- **file_count_delta:** +8684 (same scope)
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** 2847 (explicit data attempts including retries; authentication excluded)
- **reversibility:** reversible (new namespace; prior data unchanged)
- **dictionary_section:** SPX-IV-MAD-2024-2026 — index IV acceleration history (2026-09-20)
- **dictionary_reconciled:** true
- **manifests_updated:** protocol_freeze.json, boundary_probe.json, first_target_check.json, endpoint_pairing_freeze/receipt/verification.json, gap_diagnostics.json, selections.json, SPXW_collection.json, request ledger and endpoint metadata, per-date derived metadata, calibration_exact/SPXW summary/verification_final, manifest.json, inventory.json
- **why:** User requested the same IV-acceleration MAD calculation on SPX itself from 2024 onward; SPXW native PM-settled contracts isolate one settlement convention.
- **coverage:** 741 dates including 60 warmup; 681 target dates; 3405 baselines;183844/184011 scored windows; baseline statuses {"ok": 3405}.
- **verification:** 13 boundary tests, frozen quote guards, exact independent rational-CDF median/MAD checks, every historical date/count ledger and score, independent OLS and prefix-causality checks; one documented lossless endpoint-pairing repair. No new threshold or B0x backtest.
- **reconciliation:** 2847 successful native responses; 0 error attempts; 0 unresolved. Bytes and hashes reconcile with inventory; old sector data remains unchanged.

Central registry/provenance commit: `82df4f5a30a95b153df5b0973c244eaead6c818b`.
