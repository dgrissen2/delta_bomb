# MAD history extension

**Execution checklist only; no download started.**

| New target sessions | Instruments |
| --- | --- |
| 2021–2024 | XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY |
| 2021–2023 | SPX, using SPXW PM-settled options only |

1. **Extend the adapters.** Verify the 2020–2024 trading calendar, including early closes. Add 60 preceding sessions in late 2020 for the first 2021 baseline. Include all regimes. Current scripts have hardcoded dates; create new adapters without editing frozen scientific code.
2. **Inventory and probe.** Reuse exact parameter/hash-matched caches, including existing sector late-2024 and SPX late-2023 warmup data. Probe historical availability for every instrument before bulk collection. Budget missing requests explicitly; use ≤4 concurrent SDK data requests and pause on gateway outages.
3. **Fetch through ThetaData SDK.** Use `option_history_greeks_implied_volatility` plus matching `option_history_greeks_first_order`: one-minute, both rights, `strike_range=30`, SOFR, version latest, default model. Preserve 09:30–14:29 ET collection and 12:59 early-close derivation. Target 30-calendar-day ATM IV with exact tenor or an 8–65-DTE bracket.
4. **Preserve the calculation.** Strict exact → strict ±2-minute neighbors → guarded original-minute recovery with 100% spread ceiling. Retain positive dollar quotes, all quality/time guards and deduplicated sources. Use `a=(b2−b1)/15`; same-instrument/hour, 60 strictly prior sessions, equal date weights, exact weighted MAD and `scale=1.4826×MAD`. Preserve availability floors; save signed and absolute magnitude separately.
5. **Verify and report gaps.** Replay baseline/date ledgers, scores, slopes, causal prefixes and overlapping caches. Report coverage by instrument/year/hour. No extrapolation or silent inner joins. Wider strike capture needs separate files and a documented amendment; endpoint repairs must preserve originals and every required counterpart.

## Save and register

Use new immutable namespaces (`<run-date>` = execution date):

```text
/Users/dgrissen/Dev/central_trade_data/thetadata/sector_iv_mad_2021_2024_<run-date>-v1/
/Users/dgrissen/Dev/central_trade_data/thetadata/spx_iv_mad_2021_2023_<run-date>-v1/
```

Store native responses, request/expiry manifests, hashes, source/support windows, baseline ledgers, scores and verification centrally. Index new targets alongside existing later history without duplicate instrument/date/endpoint rows.

- Read the [data-root contract](/Users/dgrissen/Dev/central_trade_data/.dataroot-contract.md) and registry before writing.
- Append a `backfill` entry per operation to [CHANGELOG.md](/Users/dgrissen/Dev/central_trade_data/CHANGELOG.md), using its complete schema: paths, byte/file deltas, API calls, coverage, manifests and reversibility.
- Update [DATA_DICTIONARY.md](/Users/dgrissen/Dev/central_trade_data/DATA_DICTIONARY.md): actual dates, instrument/root, formula/units, schemas, counts, gaps and links. Reconcile before setting `dictionary_reconciled: true`.
- Commit registry and provenance together in `central_trade_data`; record the commit in the project report. Only then declare completion. No strategy tests.

**Reuse:** [sector adapter](/Users/dgrissen/Dev/delta_bomb/outputs/sector_iv_mad_remaining_2025_2026_2026-09-19/pipeline.py), [SPX adapter](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/spx_mad.py), [reproduction/repair instructions](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/REPRODUCTION.md).
