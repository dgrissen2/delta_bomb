# Full-population IV comparison, frozen before new outcomes are joined

2026-09-19. User objective: balance opportunity count and +5 SPX points before
−10 within sixty native minute bars. No penalty for price action after +5.

## Population and controls

Use the immutable 421-date selected_days.csv from branch_b_2024_halfyear_2026-09-19-v1;
411 research dates and ten separately reported development dates. These are all
dates qualifying under the inherited provenance, native coverage and session rules,
not every calendar date. Use branch_b_stop10_2026-09-19-v1 outcomes and identities.
Primary entry gate: every native low since 09:30 before entry strictly above that
day's causally available VT, plus entry open above VT. Deduplicate variant/date/minute.
No future full-session VT restriction. Same-minute double barriers remain ambiguous;
timeouts and ambiguities remain in N. These data have already been examined: this is
an expanded descriptive comparison, not an untouched holdout or an optimization.

Apply identical IV context to all thirteen frozen B01–B10 variants. B03/staircase
includes the existing thrust/staircase mode. Use all entries, first qualifying entry
per day, and greedy sixty-minute spacing as prespecified alternatives; filter before
thinning. Report raw counts, targets retained, adverse/timeout counts, six half-years,
observed/no/unknown coverage and whole-date uncertainty. Compare IV yes versus no
and measured-cohort baseline as well as the entire unfiltered family.

## Measurement, window and hypotheses

Fixed eleven ETFs: XLC XLY XLP XLE XLF XLV XLI XLB XLRE XLK XLU.
Thirty-calendar-DTE ATM-spot and native ±25-delta wings, original variance/total-
variance interpolation, nearest dated-listed expiry bracket within 8–65 days, no
extrapolation. Native ThetaData Python SDK IV and first-order Greeks, one minute,
both rights, strike_range=30, SOFR, provider latest/default dividend model. Reuse
hash-verified exact-parameter native caches; never overwrite older data.

At entry T the reference is T−35 through T−6 inclusive. This preserves the original
B06 thirty-minute pre-breakout reference; application to other families is a new
transfer hypothesis. T<10:05 is unknown. The breakout update is T−5 through T−1.
No filling outside a declared window or using a later measurement at original entry.
Native collection ends 14:29; later unavailable windows remain unknown.

Primary registry (each distinct variant remains visible, no best threshold search):

* Original ATM second-half slope <0 in ≥6 and ≥8 sectors; second-half slope <0 AND
  acceleration <0 in the same ≥6/≥8 sectors. Acceleration=(second fifteen-point OLS
  slope−first fifteen-point OLS slope)/15. Entire thirty-point support required.
* Full-window falling/rising ATM, put richness, call richness and risk reversal;
  ≥6/≥8 sectors. Falling/rising AND accelerating or slowing in the latest half,
  ≥6/≥8. Positive stress cells are diagnostic comparisons, not bullish endorsement.
* Quote-envelope-resolved ATM declines and acceleration as stringent diagnostics.
* ATM primary falling/acceleration rules under original, midpoint recovery,
  guarded recovery (spread/provider midpoint ≤100% or ≤50%), and balanced nearby-
  first recovery. Recovery is a measurement sensitivity, not another independent
  signal. Preserve original same-contract prior-minute shock checks. Balanced uses
  exact strict, then strict ±2 within the same hour block and reference window,
  then guarded-100 exact fallback; unique actual timestamps and actual-time OLS.
* Paired same-sector positive endpoint price return AND negative endpoint IV change,
  ≥6/≥8. Compare with price-only breadth, price/IV disagreements, sector recruitment,
  and IV acceleration within the broad-falling group at equal falling-sector counts.
* Strict majority (>50%) of prior-session IVV equity sector weights falling or falling
  and accelerating. Weights are a historical index proxy, publication/revision timing
  is uncertified; missing index mass never redistributed. Failed historical issuer
  snapshots remain unavailable, never substituted with today's weights.
* Balanced acceleration normalized by 1.4826 MAD of the preceding sixty NYSE sessions,
  same ETF/hour block, both signs, equal total mass per date, exact integer weighted
  median. At least ten contributing dates and positive scale. All-regime history.
  New exploratory filters: falling and accelerating with downward magnitude ≥1 or ≥2
  in ≥6/≥8 ETFs. These fixed conventional cutoffs are new tests, not inherited wins.
* Contemporaneous five-minute breakout confirmation: original six-sector IV falling
  in reference AND six-sector falling breakout slope. Available at T. A T+15 paired
  confirmation has a new entry price/clock and requires a fresh +5/−10 sixty-minute
  score and strict VT through that new entry. Never relabel old entry using future IV.

All count thresholds use fixed eleven-denominator three-state bounds: yes when
observed qualifiers suffice, no when qualifiers+missing cannot suffice, else unknown.
For known false conjuncts the conjunction is false even if the other leg is unknown.
Different IV descriptors are related coordinates, not independent confirmations.

## N expansion and comparisons

For each fixed primary ATM falling/acceleration measurement rule and paired-price
rule, report (a) B06 acceptance, (b) each other price family, and (c) unions of thrust
with IV-qualified B06, B09, or B10 breakout, and all three candidate families together.
Deduplicate executions by date/minute and assert identical outcomes. Also report the
incremental entries outside thrust alone. Do not select the best union retrospectively.
A filter cannot increase N relative to its own unfiltered universe; unions can increase
N relative to the selective thrust baseline. No new invented entry generator.

Matched B06 check: exact rising-sector count, ≤10 bps signed median sector-return gap,
one-to-one without replacement, maximum pairs then minimum gap using prior algorithm.
Freeze identities before attaching outcomes. Replicate global matching and separately
match within half-years; report remaining pairs. This is observed control, not causality.

## Coverage and audit

Collect research dates first, then all-regime historical support for magnitude:
60 prior sessions before 2024 plus 2024–2026 through September 18. 2023 Q4 calendar
uses NYSE issuer calendar (Nov23/Dec25 closed, Nov24 13:00 close):
https://ir.theice.com/press/news-details/2022/NYSE-Group-Announces-2023-2024-and-2025-Holiday-and-Early-Closings-Calendar/default.aspx
Later calendars inherit the verified study calendar including 2025-01-09 closure.
At most two concurrent SDK calls, immutable new central namespace, bounded transient
retries; stop on systemic service/authentication failure. Such failures are collection
gaps, not proof a historical measurement does not exist. Preserve per-sector/day status.

Use tests for missingness, window causality, exact denominators, union deduplication,
and prior-only normalization. Freeze feature/source hashes before outcome analysis;
independently reconcile aggregate counts and selected native outcomes. Send scoped
implementation to requested Claude review; fix material findings before conclusions.

## Ideas not silently converted into rules

Full constituent surfaces, alternative monthly-only expiry construction, short-tenor
versus thirty-day term structure, and sector/constituent leadership selection were
discussed but lack a frozen executable entry rule and/or required native contracts.
Inventory them explicitly in findings. This run tests the existing ETF coordinates
and defined transfers; it cannot claim an entire continuous surface or unspecified
constituent strategy was tested. No outcome-driven repair/threshold selection.
