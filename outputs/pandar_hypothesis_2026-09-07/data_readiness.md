# Local data readiness: HIRO stock hypothesis research

Audit date: 2026-09-07. Quant data-integrity lens, canonical persona `/Users/dgrissen/.config/skillshare/personas/strategy/quant.md`. **No network requests, no outcome quote requests, and no outcome columns read.** This audit read local earnings metadata, HIRO timestamps and pre-outcome surface columns only.

**The user now authorizes a retrospective actual-event earnings exclusion, with missing earnings refreshed from ORATS. Research may proceed under that policy.** The strict as-known schedule diagnostic remains zero; it is not the admission policy for this authorized retrospective sample. Older stock HIRO exists: 334 stock-dates for 180 current-HIRO stocks on June 12–18, 2026. After the authorized root-owned metadata refresh, the deterministic preliminary population contains **50 signals across 50 stocks and five June entry dates**. Exact-contract, minute-validity and execution gates remain downstream. Signal-date bounds are 2024-01-02–2026-08-05; both signal and actual-entry dates require no observed earnings in the inclusive next 30 calendar days and complete metadata coverage through that horizon. The root owns all batched API requests under the user’s 2,000-total-call authorization.

## Earnings metadata

Frozen membership: `/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_skew_journey_2026-09-06/hiro_universe.csv`, 398 instruments, 323 stocks. It is the recent HIRO set applied backward, not historical membership.

| Local source | Total rows | Current HIRO-stock rows / names | HIRO date range | Admission implication |
|---|---:|---:|---|---|
| Daily next-earnings snapshot | 1,041,918 | 329,416 / 101 | 2007-01-03–2026-07-29 | Zero dated nextErn values |
| Central earnings-long | 178,141 | 18,192 / 191 | 1987-09-03–2026-06-25 | Actual event history; no as-known timestamp |
| PIT-constituent event history | 119,871 | 7,569 / 123 | 1984-03-31–2026-07-29 | 1,197 events from 2024 onward; zero updatedAt timestamps before their event |

Exact paths:

- `/Users/dgrissen/Dev/central_trade_data/orats/stable_rrs_earnings_2026-07-29-v1/normalized/earnings.parquet`
- `/Users/dgrissen/Dev/central_trade_data/orats/earnings/earnings_long.parquet`
- `/Users/dgrissen/Dev/central_trade_data/orats/earnings/pit_constituents_earnings_long.parquet`

The daily source has 24,972 HIRO rows / 100 stocks in 2024, 24,631 / 99 in 2025, and 14,157 / 99 in 2026 through July 29. **Every year has zero dated nextErn values**, including earlier history. One checked raw gz response has `nextErn=0000-00-00`; normalization turned those values into null. The manifest's date range is row coverage, not dated-calendar coverage.

Alternative checks: `/Users/dgrissen/Dev/central_trade_data/orats/cores_history` contains 170,904 HIRO rows / 40 stocks with the nextErn field, 2007-01-03–2026-04-24; all are placeholders. `/Users/dgrissen/Dev/central_trade_data/orats/delta_bomb_refresh_2026-08-17/NVDA_cores.parquet` has 4,934 rows, also all placeholders. Slim core/summaries tables omit the earnings field.

The root agent checked [official ORATS definitions](https://orats.com/docs/definitions), which say nextErn requires another subscription. This is a documented possible explanation for the zeros; account entitlement was not verified. Treating these solely as stale snapshots would misdiagnose the limitation. Actual event tables should be unioned/deduplicated for a retrospective event purge; their names and `updatedAt` fields do not establish historical schedule versions. A current `/hist/earnings` refresh could support that separate retrospective purge, but does not establish as-known admission.

## Archived individual-stock HIRO

The targeted scan found 1,304 normalized files, 1,344 unique stock-dates, 246 current-HIRO stocks, and dates 2026-06-12–2026-09-04. June coverage lives under `/Users/dgrissen/Dev/HIRO_finder/output`; August/September coverage lives under `/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/replay`. There were no 2024/2025 normalized individual-stock series in those targeted roots. Index archives and reconstructed chart images do not qualify as individual-stock HIRO.

| Session | Stocks with timestamp-bearing series |
|---|---:|
| 2026-06-12 | 81 |
| 2026-06-15 | 73 |
| 2026-06-16 | 76 |
| 2026-06-17 | 99 |
| 2026-06-18 | 5 |
| 2026-08-21 | 35 |
| 2026-08-24 | 38 |
| 2026-08-25 | 41 |
| 2026-08-26 | 44 |
| 2026-08-27 | 154 |
| 2026-08-28 | 116 |
| 2026-08-31 | 171 |
| 2026-09-01 | 174 |
| 2026-09-02 | 91 |
| 2026-09-03 | 20 |
| 2026-09-04 | 126 |

Example June source: `/Users/dgrissen/Dev/HIRO_finder/output/hiro_date_specific_scrapes_2026-06-12_to_2026-06-16/date=2026-06-12/2026-06-18/100433Z/normalized/AA_series.csv`.

The machine-readable manifest `/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/hiro_archive_coverage.csv` maps every unique ticker/session to a selected source path. The JSON retains all alternate source records. Selection prefers more unique timestamps, then later ending coverage and deterministic path order. This is a presence manifest, not a completed intraday validity gate: some captures start late, extend after hours, mix groups, or contain multiple session dates. Dates were derived from UTC timestamps converted to America/New_York rather than assumed from directory names. Validate the selected `all` group, regular-session coverage, timestamps, missing intervals and capture/version provenance before a timing replay.

## Pre-outcome population intersection

These are availability diagnostics using only existing `eligible==True` and `wing_rank>=85` columns from `/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_skew_journey_2026-09-06/daily_features_and_outcomes.parquet`:

- Same-session high-skew/HIRO overlap: 143 stock-dates / 89 stocks; 74 stock-dates before August.
- High-skew EOD signal followed by next-session archived HIRO: 165 signals / 96 stocks; 72 before August.
- Of next-session candidates, 36 have stock-HIRO date presence on each of four sessions; 11 on each of five. Before August those counts are 5 and 0.
- After strict as-known dated earnings clearance at signal and entry: **0**.

These are not admitted trades or performance counts. Closing EOD features cannot authorize an earlier same-day order. Continuous-session counts are presence-only, before exact contracts, corporate actions, quote validity, entry constraints and earnings. The session map uses observed surface dates plus archived HIRO session dates through September 4. Full four/five-session HIRO is unnecessary if the frozen rule only requires HIRO through second-leg timing; root should specify that causal window instead of dropping dates mechanically. All candidate pairs are retained in JSON, so no random four-name subset is needed.

## Provider capabilities and missing metadata

Local public interface sources: `/Users/dgrissen/Dev/ThetaData/openapiv3.yaml` and `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/lib/python3.13/site-packages/thetadata/client.py`.

- **Date-specific contract presence:** `option_list_contracts(request_type="quote", date, symbol=[...], max_dte=None)` returns symbol, expiry, strike and right for contracts quoted on that date. `option_list_dates("quote", symbol, expiration, strike, right)` and `stock_list_dates("quote", symbol)` report data-available dates. Undated expiration/strike lists cannot prove that a strike already existed on a signal date. Quote presence is not official listing history, and no quotes is not proof of no listing.
- **Exact Greeks:** `option_history_greeks_first_order` supports symbol, expiry, date, interval, exact strike/right and start/end time; the project uses identical start/end times for exact-minute checks. First-order IV/delta uses midpoint inputs. `option_history_greeks_implied_volatility` separately returns bid, mid and ask IV, underlying timestamp/price and IV error. The local OpenAPI labels Greeks standard tier and quote/list-contracts value tier; account entitlements were not queried.
- **Underlying and quotes:** Greek rows carry underlying timestamp/price; stock history/at-time quote interfaces can align stock NBBO. Historical option quote rows contain bid/ask, sizes, exchange and conditions. Interval samples are the last quote at each interval timestamp; a complete minute grid does not establish freshness or execution.
- **ORATS exact EOD chain:** `/datav2/hist/strikes` returns strike, expiry, DTE, delta/Greeks, call bid/ask price and size, bid/mid/ask IV, stock/spot prices, quoteDate, updatedAt and expiryTod. This was verified in cached row schema. `/Users/dgrissen/Dev/central_trade_data/orats/strikes` alone has 2,163 dated files / 49 HIRO stocks, 2023-02-27–2026-04-22, concentrated in prior study windows; other strike caches exist and were not comprehensively inventoried. This is not uniform historical full-chain availability.
- **Forwards:** root checked the official ORATS `/hist/monies/implied` interface, with expiry-specific riskFreeRate, yieldRate, residualYieldRate and stockPrice. Validate carry signs before deriving forward; do not use strike residualRate as plain risk-free rate or silently equate spot with forward.
- **Deliverables/splits:** no corporate-action, option-deliverable, split or multiplier endpoint appears in the inspected Theta OpenAPI. Targeted central reference files contain index membership, not OCC deliverables. Adjusted/unadjusted daily prices support price-basis checks but cannot establish contract multiplier or stock/cash deliverables. A dated security identity and OCC adjustment ledger is still needed for selected contracts and split/rename periods.

## Targeted metadata fetch priorities

1. For any separate as-known sensitivity, verify the next-earnings product and version semantics. This is optional research context and does not block the user-authorized actual-event cohort. Do not repeat full core history solely to retrieve the same placeholders.
2. The user has explicitly authorized root to refresh `/hist/earnings`, batched across the 323 HIRO stocks within the shared 2,000-total-call budget. The earlier 33-call figure was the expected ten-stock-batch earnings tranche, not the current total authorization. Preserve raw payloads, updatedAt, retrieval timestamps and hashes; use resulting exclusions as actual-event-purged research.
3. For frozen candidate dates, request Theta contract identities/date availability before quote outcomes. Save failures as no-data metadata rather than substituting another root, expiry or strike.
4. Resolve dated listing/rename and OCC split/deliverable metadata for candidate contract lifetimes; reject unknown deliverables until established.
5. Check SpotGamma retention/product metadata before attempting 2024/2025 stock-series backfills. `/Users/dgrissen/Dev/HIRO_finder/hiro_tickers/historical_backfill.py` provides a date-specific `/v11/hiro` interface with `syms,start,end,all=1,nextExp=1,retail=1`; interface availability alone does not prove old dates exist. Actual series requests are not part of a metadata-only budget.

No shared code/configuration was edited. Deliverables are this report, its JSON evidence/counts, and the normalized HIRO path manifest in `/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07`.


## Authorized refresh implementation update

Root's ORATS probe found that `/hist/splits` is not batch-safe for this API/account: a comma-separated AAPL,NVDA request returned an empty result while the individual AAPL request returned its known splits. The root-owned downloader therefore uses batched earnings and individual split requests for the 55 pre-August high-skew/next-session-HIRO candidate stocks. Other stocks retain `splits_status=not_requested_no_eligible_hiro_signal`; they are not silently marked split-free. No global skill was edited.

The first refreshed earnings file contained nine `earnDate=0000-00-00` placeholders. The population freezer rejected the metadata before publishing. Root then quarantined those rows in `/Users/dgrissen/Dev/delta_bomb/data/pandar_hypothesis_2026-09-07/earnings_invalid_dates.parquet` and produced 26,510 valid earnings rows for 315/323 stocks, using no additional provider calls for normalization. This is an input-integrity correction, not a change to the authorized actual-event admission policy.


## Completed population freeze

`/Users/dgrissen/Dev/delta_bomb/scripts/pandar_hypothesis_population.py` reads only explicitly allowed pre-outcome columns and retains all 41,864 supplied ledger rows. Root-authorized rules additionally require positive absolute call wing. It selected 50 signals, retained 17 otherwise-eligible signals with a holding-window-overlap reason, and retained 41,797 failed-filter rows. Earlier rejected candidates do not consume an episode or block later dates. The 50 selected signals span 50 stocks and five entry dates: June 12 (19), June 15 (15), June 16 (5), June 17 (10), and June 18 (1). This remains below the protocol's 20-distinct-entry-date statistical threshold.

Artifacts: `/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/population_ledger.csv`, `/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/selected_population.csv`, `/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/future_earnings_horizon.csv`, and `/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/population_manifest.json`. The manifest records input/output and implementation hashes; input hashes are checked again before publishing. Fourteen causal/boundary tests pass in `/Users/dgrissen/Dev/delta_bomb/tests/test_pandar_hypothesis_population.py`, and Ruff passes. No provider calls were made by the freezer.


## HIRO retention and safe historical interface audit

This additional audit made no requests. The existing loader is `/Users/dgrissen/Dev/HIRO_finder/hiro_tickers/live_browser.py::connect_hiro_browser_session`. Its default CDP port is 9923; pass the existing absolute profile `/Users/dgrissen/Dev/HIRO_finder/output/chrome_hiro_monitor_profile` because the default path is relative. `navigate=False` can reuse the dashboard. The loader may launch Chrome or require manual login if no usable session exists; it is not a headless credential bypass. Closing its session stops Playwright while leaving Chrome available.

`/Users/dgrissen/Dev/HIRO_finder/hiro_tickers/historical_backfill.py::fetch_historical_hiro_payload` reads `sgToken` inside browser JavaScript, performs the authenticated request and returns response JSON, without returning the token to Python. The endpoint is `https://api.spotgamma.com/v11/hiro`, with one `syms` value, `start=end=YYYY-MM-DD`, `all=1`, `nextExp=1`, `retail=1`. **Only one symbol per request is validated by this wrapper; the multi-symbol limit is unknown.** Never infer a batch entitlement from a plural parameter name.

The response contains symbol-keyed group arrays. `capture_historical_session` requires a single date and records empty arrays as unavailable. `inspect_series_csv` checks that offset-bearing timestamps map to the requested Eastern session; it does not establish full regular-session coverage. Both successes and unavailable responses are cached, so an intentional re-probe needs `force=True` or a separate output directory. Override the S&P 500 symbol/output defaults for individual stocks and count retries in root's shared request budget.

A concrete retention receipt is `/Users/dgrissen/Dev/HIRO_finder/output/hiro_spx_history_2026-08-05_to_2026-08-18/manifest.json`. On August 19, 2026 at 08:36–08:37 UTC, the S&P 500 requests for August 12, 13, 14, 17 and 18 succeeded, while August 5, 6, 7, 10 and 11 returned zero rows. This is **consistent with five-session retention for that index/account/capture date**, not proof of the retention limit for every stock or entitlement.

The June stock receipt `/Users/dgrissen/Dev/HIRO_finder/output/hiro_date_specific_scrapes_2026-06-12_to_2026-06-16/date=2026-06-12/2026-06-18/100433Z/manifest.json` requested June 12 and was created June 18 at 10:04 UTC, completing at 11:29 UTC with 101 captures. These were contemporaneously nearby historical captures; their existence does not show June data remains retrievable in September. No 2024/2025 normalized stock archive was found in the targeted roots.

Recommended bounded extension probe, owned by root: use one known-live stock on a recent completed session as a positive control, the same stock on a known June archive date, and one older date. Preserve HTTP status, requested/returned dates, row counts and capture time. If the recent control works and older dates are empty, stop broad historical requests and resolve retention or archival access first. No probe was run here.

The separate exact-contract audit is `/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/contract_reference_audit.md`, with machine-readable JSON and CSV alongside it. All 98 frozen legs have ORATS signal tuples; no dated authoritative deliverable inventory was located. Concrete flags include the old/current SERV issuer collision and DVN versus 70-share DVN1 after the May 2026 Coterra merger. These flags do not alter the frozen population or protocol.
