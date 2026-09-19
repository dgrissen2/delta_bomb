# Sampling and collection provenance

Frozen 19 September 2026, before new IV classifications and outcomes. Working-set/protocol commit: 998c31b.

## Population and draw

The recorded VT archive contains 424 dated sessions in the requested 2025–2026 window: 250 in 2025 and 174 in 2026. Its last available date is 2026-09-11, although the protocol allowed completed dates through 2026-09-18. No missing VT date or level was invented.

The audit preserved the original same-date pre-open note corroboration and 09:30 SPX OPEN strictly above VT requirements. After completing the price inventory, there were **104 eligible new dates**: **69 from 2025 and 35 from 2026**. The original fifty and earlier ten exploration dates were excluded.

One uniform draw without replacement selected **100 dates: 66 in 2025 and 34 in 2026**. Combined with the original fifty, the study contains **150 dates: 66 in 2025 and 84 in 2026**. The stored 64-bit sampling seed is **16327036225962936691**. The four eligible dates not drawn are **2025-09-10, 2025-09-11, 2025-12-30, 2026-04-16**.

The first and last additional dates are 2025-02-06 and 2026-08-11. No sampled date was replaced based on sector data, B06 count, or outcome.

| Month | Additional sampled dates |
| --- | ---: |
| 2025-02 | 8 |
| 2025-08 | 3 |
| 2025-09 | 14 |
| 2025-10 | 20 |
| 2025-11 | 7 |
| 2025-12 | 14 |
| 2026-01 | 4 |
| 2026-04 | 9 |
| 2026-05 | 9 |
| 2026-06 | 4 |
| 2026-07 | 5 |
| 2026-08 | 3 |

This is a sample of the **documented eligible universe**, not a uniform sample of every above-VT session that may have existed in 2025–2026. In particular, most 2025 coverage is from August–December; the sample has eight February dates and no March–July dates. Missing/conflicting pre-open provenance and the above-VT-at-open criterion limit coverage. The population ledger preserves individual reasons, including overlapping exclusions. Do not label this balanced full-year regime coverage.

## Native SPX coverage before the draw

The original cache plus earlier normalization covered 360/424 recorded dates completely. The SDK returned raw data for all 64 requested coverage checks. Sixty passed the inherited normalization; four raw responses failed OHLC validation:

| Date | Invalid OHLC observations reported |
| --- | ---: |
| 2025-04-07 | 4 |
| 2025-07-03 | 179 |
| 2025-11-28 | 180 |
| 2025-12-24 | 179 |

The failures remain recorded with raw data preserved. They were not repaired by filling or dropping observations until a nominally complete day appeared. Some of these dates have pre-existing partial native sessions and remain incomplete in the final ledger. The final full-session inventory is **420/424**: 246/250 in 2025 and 174/174 in 2026. Completing the inventory did not enlarge the eligible above-VT set beyond 104 because the other dates failed remaining eligibility criteria.

## Frozen signals, before scoring

Original fifty: **374 B06 parents**, 49 active dates. Additional 100: **666 parents**, all 100 active dates. Combined: **1,040 parents**, 149 active dates. July 13, 2026 remains the original zero-event date. The busiest new date has fifteen entries; the busiest original date has twenty-two. The original 374 identities, entry minutes, entry prices, and boundaries reproduce exactly.

The parent counts are not independent observations. Outcomes are not used to select dates, generate parents, or decide whether to fetch sector IV.

## Dated option listings

All 100 dated listings were obtained through the ThetaData SDK before the histories. Of 1,100 new sector-days, 22 have no permitted expiry bracket: twenty XLRE and two XLB. They remain sampled and will be missing IV panels rather than replacement dates.

There are **1,941 selected date/sector/expiry pairs**, each requiring midpoint/bid/ask IV and first-order Greeks at native one-minute resolution: **3,882 planned history responses**, in addition to the 100 listings. The new request cache is:

/Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_2026-09-19-v1/

An expiry gap can be imposed by the fixed rules rather than an API failure. On **2025-02-14**, both XLB and XLRE have listed expirations **2025-02-21 (7 DTE)** and **2025-03-21 (35 DTE)**. The 8-day minimum excludes the first. The second alone cannot bracket 30 days, so those sector-days remain unknown. We did not loosen the minimum to admit the seven-day expiry. The 22 missing sector-days occur on twenty distinct sampled dates; other sectors can still establish six known qualifiers on those dates.

The collection manifest records progress and final errors; this note does not assert that a running download has finished. Final coverage, completed requests and results belong in FINDINGS.md and verification.json after collection.

## Immutable evidence

The selection and eligibility artifacts are selected_days.csv, population_ledger.csv, random_draw_order.csv, sampling_seed.json, sampling_manifest.json, sampling_input_hashes.json, and vt_note_provenance.json in this slug. Raw and normalized native SPX data are stored centrally. The full expanded signal identities and counts are b06_parents.csv, combined_days.csv, day_event_counts.csv, and parent_freeze.json.

No fixed rule or threshold is changed by this sampling audit.
