

## SPX-IV-MAD-2024-2026 — index IV acceleration history (2026-09-20)

Namespace: `/Users/dgrissen/Dev/central_trade_data/thetadata/spx_iv_mad_2024_2026_2026-09-20-v1`. Project producer/report: `/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20`.
Underlying **SPX**, option root **SPXW** (PM-settled index options only).
681 target sessions January 2, 2024–September 18, 2026; 60 strictly prior warmup
sessions October 5–December 29, 2023; 741 calendar dates total. All regimes.
Native 09:30–14:29 ET; derived early-close cutoff 12:59. Thirty-minute endpoints
begin 09:59. No claims about uncollected later-session hours or future 2026 dates.

Native ThetaData SDK IV and matching first-order histories, one-minute interval,
both rights, strike_range=30, SOFR/latest/default model. Listed expiries bracket
30 calendar DTE within 8–65 DTE; exact 30 DTE uses one expiry. Same frozen ATM spot-strike
interpolation, call/put variance average and quote guards as the sector baseline.
Strict exact→strict±2min neighbor→guarded original-minute recovery, 100% spread
ceiling for fallback. Positive dollar bid/ask required; no zero-bid substitution.
Sources stay inside actual window/hour; unique actual timestamps. Actual-time
OLS fifteen-minute halves; acceleration=(b2−b1)/15.

Sixty strictly prior sessions per endpoint-hour, both signs, equal total date
weights; exact lower weighted median and MAD. Scale=1.4826×MAD; minimum 10
contributing dates and scale>1e−12. Signed score=−a/scale; absolute=abs(a)/scale;
downward-only requires actual falling IV and negative acceleration. Unknowns
retain expected slots and reasons. No thresholds or B0x outcomes fitted.

**Coverage:** 183,844/184,011 target windows
scored; 3,405 daily/hourly baseline rows;
baseline statuses `{"ok": 3405}`.
Target dates missing selected expiry brackets: 0.
Raw response counts/rows: `{"option_history_greeks_first_order": {"responses": 1053, "rows": 37167600}, "option_history_greeks_implied_volatility": {"responses": 1053, "rows": 37210800}, "option_list_contracts": {"responses": 741, "rows": 8849576}}`.

**Files:** native endpoint Parquet plus request metadata; immutable requests.jsonl;
dated listed expirations and selected brackets; day input manifests; per-date
native-derived IV sources, source choices/support and acceleration windows;
all_windows/daily_coverage; calibration_exact/SPXW/block_baselines.parquet and
scored_windows.parquet; CSV baselines/coverage/half-year bins; independent
verification, boundary probes, protocol and input/output hashes. Project links
reference central outputs without duplicating market data.

Score schema: `{"acceleration": "float64", "available": "bool", "b1": "float64", "b2": "float64", "block": "int64", "date": "str", "downward_magnitude": "float64", "end_min": "int64", "fallback_slots": "int64", "historical_median": "float64", "history_days": "int64", "mad": "float64", "maximum_shift_minutes": "int64", "n_first": "int64", "n_second": "int64", "neighbor_slots": "int64", "recovered_source_minutes": "str", "scale": "float64", "score_status": "str", "signed_score": "float64", "source_minutes": "str", "span_first": "int64", "span_second": "int64", "start_min": "int64", "status": "str", "supported_slots": "int64", "symbol": "str", "unique_sources": "int64"}`.

**Verification:** 13 boundary tests, inherited quote-guard checks, all
baseline medians/MADs independently checked using rational-CDF inequalities;
all prior-date/count ledgers and scores checked; independent OLS and causal prefix
replay, including 2023/2024 boundaries. Frozen sector scientific code unchanged.

One recorded endpoint alignment exception: June 9, 2026 has 79,200 native IV rows
versus 36,000 native Greek rows, with every Greek key present in IV. A separate
paired IV view keeps every Greek key and unchanged IV values; original native
responses remain immutable. The additive protocol freeze, receipt and independent
verification record the 43,200 IV-only rows excluded, with no Greek inference,
quote-guard change or extra request. All 271 windows on that date are available.

**Calls:** 2847 explicit SDK data attempts,
2847 successful responses,0 error
attempts, 0 unresolved. Authentication excluded. Existing exact parameter-matched
caches are reused by SHA-256. Four SDK/two calculation workers, 12,000-attempt cap,
two normal attempts plus one exclusive cooled INTERNAL-only third; gateway
outages pause requests. Zero ORATS/other paid-provider calls.

**Payload:** 8,684 files, 2,197,682,952 bytes, excluding this namespace's
inventory/dictionary and root registry markdown. Per-file hashes in inventory.json.
Operation is reversible additive backfill; no prior source or sector data changed.
