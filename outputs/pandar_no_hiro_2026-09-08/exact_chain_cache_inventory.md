# Exact-chain cache inventory without HIRO requirements

Audit date: 2026-09-08. Original 323-stock membership set retained. No API calls. This audit inspects file schemas and only ticker/date identifiers, record counts and presence. It reads no option price paths or trade outcomes. JSON payloads are decoded solely to extract metadata; parquet reads project ticker/tradeDate only.

## Available chain sources

| source | files | ticker_dates | stocks | dates | first | last |
| --- | --- | --- | --- | --- | --- | --- |
| central_strikes | 2163 | 2163 | 49 | 61 | 2023-02-27 | 2026-04-22 |
| deustrader_wins_recreate_20260823 | 114 | 114 | 2 | 57 | 2024-12-04 | 2026-03-20 |
| pandar_call_exclusion_audit | 17 | 56 | 33 | 17 | 2026-08-11 | 2026-09-03 |
| pandar_call_search_expansion | 44 | 357 | 130 | 18 | 2026-08-11 | 2026-09-03 |
| pandar_early_put_backfill | 90 | 803 | 155 | 9 | 2026-08-11 | 2026-08-21 |
| pandar_mstr_prior | 77 | 77 | 1 | 77 | 2026-05-15 | 2026-09-03 |
| pandar_richness_hist_strikes | 1 | 756 | 6 | 129 | 2025-12-09 | 2026-06-15 |
| pandar_signal_chains | 1 | 50 | 50 | 5 | 2026-06-11 | 2026-06-17 |
| squeeze_chains | 87 | 94 | 39 | 87 | 2018-08-14 | 2026-01-29 |
| squeeze_chains_control_entry | 483 | 988 | 131 | 254 | 2018-02-12 | 2026-03-04 |
| squeeze_chains_funnel_entry | 176 | 203 | 77 | 175 | 2018-01-02 | 2026-03-04 |
| squeeze_chains_funnel_forward | 640 | 791 | 20 | 543 | 2018-08-20 | 2026-01-12 |
| squeeze_chains_liquid | 852 | 1414 | 139 | 809 | 2018-01-03 | 2026-03-04 |

Distinct available stock-dates: 7632. Distinct stocks: 257. Distinct dates: 1372.

The central `orats/strikes` store contains JSON files, not parquet. All 2,163 files within the original membership were nonempty; this store alone covers 49 stocks and 61 dates. It supplies 1,042 signal-stock cases on 31 signal dates across 48 stocks from 2024 onward with chains present on signal and every following five sessions. Those stocks are outside the six names previously selected for the June replay.

## Session-continuous pricing candidates

A presence candidate requires chains on signal day and every one of the following five observed exchange sessions. Entry is next-session EOD; fourth/fifth holding-session exits are signal+4/+5 sessions because entry counts as holding session one. The calendar comes from the 921-date broad summaries panel; it is an availability calendar, not a substitute for a separately maintained exchange calendar.

- 2024 onward, price fields throughout: 2,158 stock-signals, 108 stocks, 319 distinct signal dates. Year counts: {'2024': 303, '2025': 400, '2026': 1455}.
- 2024 onward, full signal and entry fields: 1,794 stock-signals, 56 stocks, 155 distinct signal dates. Year counts: {'2024': 247, '2025': 331, '2026': 1216}.
- 2024 onward, full fields throughout: 1,787 stock-signals, 55 stocks, 148 distinct signal dates. Year counts: {'2024': 242, '2025': 329, '2026': 1216}.
- Outside prior six, full fields throughout: 1,055 stock-signals, 49 stocks, 38 distinct signal dates. Year counts: {'2024': 242, '2025': 243, '2026': 570}.

These are availability counts before earnings, signal eligibility, contract lifetime, expiry/strike continuity, liquidity or nonoverlapping episode selection. They are not admitted trades. A full chain existing each day does not guarantee the same selected strike remains listed/quoted; expiry and changing DTE filters can remove it. Keep failed selections and missing exact contracts.

## Schema and scope cautions

Full diagnostic fields mean ticker, tradeDate, expiry, strike, stockPrice, call bid/ask, displayed bid/ask size, delta, vega, gamma, bid/mid/ask IV, smvVol and quoteDate are present in the file schema. This confirms availability of fields, not valid values or freshness. The full-schema flag is retained per file in the CSV.

The `squeeze_chains_funnel_forward` cache has a reduced schema: bid/ask prices, delta, callMidIv and stockPrice, but no displayed sizes, quote timestamps, gamma/vega or bid/ask IV. It can supply a limited EOD price reference, but cannot clear the same execution/strike-richness diagnostics as the full chains. Other squeeze chain sources have full ORATS schema in the audited files.

The older Pandar call-search, call-exclusion, early-put and MSTR-history JSON caches likewise lack call sizes, quoteDate, gamma and vega. They retain price references but are not equivalent to full diagnostic chains. `skew_calibration_strikes` was inspected and retained in the inventory with failed price-schema flags: its files omit call bid/ask prices and IVs, so it does not enter the quoted-price availability counts. All 2,163 central-cache ticker/date identifiers matched their filenames. Squeeze acquisition manifests explicitly describe unfiltered full chain payloads for the full-schema sources; the forward source is explicitly projected.

The central recent-window manifest declares all deltas with 5–180 DTE; earlier windows and other sources may differ. Source completeness across every listed expiration is not established. Original strike snapshots have 1–35 DTE and contain six previously selected stocks, 126 dates each. Neither the broad summaries nor the source `call_kink` term spread establishes local strike curvature. Use exact strike neighborhoods and bid/ask uncertainty for that measurement.

All these caches were acquired for prior studies, including stress windows, squeeze selection, and selected Pandar screens. Cache presence is a sampling constraint, not random or full-market coverage. Do not label the resulting sample an untouched holdout or unbiased history. A deterministic union of existing files can be frozen before new outcome analysis.

EOD bid/ask references are not executable-fill proof. Quote condition/staleness, contract deliverables, split/rename identity and early assignment remain separate checks. Preserve unavailable cases rather than substituting a neighboring or renamed contract.

Suggested first exact-contract followup: freeze the full-field signal/entry population and a common holding deadline, choose strikes from signal chains only, preserve exact identifiers into the next EOD entry and all exits, then compare wing-only repricing against realized quoted economics. Keep raw-richness and target-delta baselines on identical opportunities. Broad surface findings supply context; they do not replace this pricing test.

## Artifacts

- `exact_chain_cache_inventory.csv`: one row per source file/ticker/date, with required-field flags and missing fields.
- `exact_chain_cache_continuous_candidates.csv`: deterministic presence candidates, with full-field flags.

No changes to prior frozen studies. Minute/Theta trees and outcome tables were excluded. Additional unenumerated project caches may exist; this is a targeted inventory of the named central and Pandar chain sources.

Parse errors: [].
