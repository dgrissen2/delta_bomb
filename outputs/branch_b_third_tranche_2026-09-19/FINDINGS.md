# Third tranche: all remaining verifiable qualifying 2025–2026 dates

Completed 19 September 2026. Same B01–B10 recipes, same13 comparison rows, same
**+5 before−15 within60 minutes** score. Posttarget reversals do not change a win.

## Result for the CIO

The third tranche contains **89 dates:88 from2025 and one from2026**. Its results
weaken the earlier favorites. B08 price re-entry fell to28/60 (46.7%), B07 reclaim
to80/154 (51.9%), B02 thrust to14/25 (56.0%), and B10 retest to7/12 (58.3%). Plain
B06 was281/540 (52.0%), close to its52.9% on the preceding100-date addition.

**B10 immediate opening-range breakout is the more consistent candidate across
the two extensions:**60.3% on the second tranche and61.4% on the third, with96/149
(64.4%) across all239 non-development dates. **B05 stall/reclaim** reached343/570
(60.2%) in tranche3, but its combined rate is57.9%. Neither comparison establishes
a causal improvement: these rules enter at different times on different dates.
The fixed-time B01 control itself reached59.1% in tranche3 and58.8% overall.

B10 retest still has the highest combined point estimate,24/32 (75.0%), but the
new7/12 result does not repeat its previous85% level. B02's combined40/58 (69.0%)
also masks a weaker new tranche. The earlier B08/B07 preference should therefore
be downgraded. No rule is promoted as validated; the evidence changed, so the
candidate assessment changes with it. The one new2026 date cannot establish
robustness in2026. This is mainly a missing-part-of-2025 extension.

## What “all qualifying days” means here

The audit covers every **429 completed NYSE session from2025-01-01 through
2026-09-18**. It identifies249 verifiable qualifying dates:50 original,100 second
tranche,89 third tranche and10 original dashboard-development dates. The primary
research total is **239 dates**; the ten development dates are scored separately
and included only in the explicitly labeled249-date descriptive total.

All qualifying dates have complete native390-minute SPX observations, positive
same-date VT supported by preopen-note labels, and an opening price above VT.
No date is added or removed because of a signal count or outcome. Fourteen of
the89 new dates have no strict-VT entry in these families; all remain in the
date-resampling universe. Qualifying dates are not required to stay above VT
after an entry, which would condition selection on the future.

The primary event gate instead checks every prior minute low from09:30 through
the minute before entry and the entry open. Each must be strictly above VT.
A prior touch/breach blocks the remainder of that date. The entry bar's later
low and future full-day status are never used to approve an entry.

This is a census of **verifiable qualifying dates**, not proof that every other
market day was below VT. Missing/conflicting evidence and incomplete prices stay
explicit. September18,2026 has no saved dated VT or SPX minute input here and
remains unknown; it is not classified below VT. Future2026 sessions cannot be
included. The unchanged full-session rule also excludes the three2025 early closes.

## Important correction to the earlier date audit

The earlier parser required a `Date` field and exact agreement with the first
heading's timestamp. Many older saved notes instead use **`Published`**, sometimes
with a later wrapper heading than the original content heading. The strict parser
reported these as missing preopen corroboration even when the file contained
usable explicit Eastern preopen publication labels and a matching SPX VT table.
That was an avoidable coverage restriction in our earlier implementation.

The new audit reads both metadata formats. It requires at least one explicitly
Eastern publication heading, correct EST/EDT calendar usage, every publication
label on the requested day, and the **latest** such label strictly before09:30.
It preserves differing preopen timestamps rather than claiming they agree.
After-open labels, wrong dates, malformed publication metadata and VT conflicts
are rejected. Scraped-at is never used to establish historical availability.
Publication labels still cannot prove that a saved article had no later revisions.

This recovers **85 additional qualifying dates**, all in2025. Seventy-five of those
new dates have a preserved preopen time discrepancy in at least one usable note.
The other four third-tranche dates were already eligible but not selected in the
earlier random100 draw:2025-09-10,2025-09-11,2025-12-30 and2026-04-16.
The parser correction is disclosed as a change to evidence ingestion; it is not
represented as the old sampler suddenly having more qualifying days.

The old50/100 numeric results remain unchanged and all reproduce. However, the
earlier claim that the recorded eligible universe had only104 new dates was
conditional on this overly restrictive parser. Much of the missing2025 coverage
was recoverable local evidence. This strengthens the need to separate calendar
mix from signal quality; it does not prove why any particular rule deteriorated.

## All13 rows: three tranches and the239-date research total

Cells show successful +5-first signals / distinct entry opportunities, then hit
rate. Overlapping same-variant/date/minute setups count once. Repeated entry times
on the same date and different families can share price paths and are dependent.

| Entry | Original50 | Second100 | Third89 | Combined239 |
| --- | --- | --- | --- | --- |
| B01 · Fixed-time control | 110/166 · 66.3% | 204/369 · 55.3% | 199/337 · 59.1% | 513/872 · 58.8% |
| B02 · Five-minute thrust | 13/15 · 86.7% | 13/18 · 72.2% | 14/25 · 56.0% | 40/58 · 69.0% |
| B03 · Thrust + staircase | 30/46 · 65.2% | 37/64 · 57.8% | 42/79 · 53.2% | 109/189 · 57.7% |
| B04 · T pullback/break | 100/152 · 65.8% | 165/310 · 53.2% | 149/295 · 50.5% | 414/757 · 54.7% |
| B05 · Stall/reclaim | 162/269 · 60.2% | 385/698 · 55.2% | 343/570 · 60.2% | 890/1537 · 57.9% |
| B06 · Immediate breakout | 167/265 · 63.0% | 263/497 · 52.9% | 281/540 · 52.0% | 711/1302 · 54.6% |
| B06 · Breakout/retest | 39/63 · 61.9% | 63/121 · 52.1% | 78/146 · 53.4% | 180/330 · 54.5% |
| B07 · Failed breakdown/reclaim | 48/75 · 64.0% | 111/186 · 59.7% | 80/154 · 51.9% | 239/415 · 57.6% |
| B08 · Band rebound, price | 18/27 · 66.7% | 44/70 · 62.9% | 28/60 · 46.7% | 90/157 · 57.3% |
| B08 · Band rebound + RSI | 1/3 · 33.3% | 4/6 · 66.7% | 5/9 · 55.6% | 10/18 · 55.6% |
| B09 · One-minute staircase | 390/599 · 65.1% | 675/1272 · 53.1% | 701/1270 · 55.2% | 1766/3141 · 56.2% |
| B10 · Opening-range immediate | 23/29 · 79.3% | 38/63 · 60.3% | 35/57 · 61.4% | 96/149 · 64.4% |
| B10 · Opening-range retest | 6/7 · 85.7% | 11/13 · 84.6% | 7/12 · 58.3% | 24/32 · 75.0% |

## Third-tranche uncertainty and outcome accounting

Intervals are95% percentile intervals from10,000 whole-date bootstrap resamples,
seed20260919. They retain zero-event dates and account for dependence within a
date, not every form of serial dependence, regime change or research selection.
The small32-entry combined retest sample remains uncertain; a high pooled rate
does not erase its weak new tranche. Year-specific third2026 intervals have only
one date and cannot support general inference.

| Entry | N | Active dates | +5 first | −15 first | Neither | Hit rate | 95% date interval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B01 · Fixed-time control | 337 | 75 | 199 | 45 | 92 | 59.1% | 53.6–64.5% |
| B02 · Five-minute thrust | 25 | 13 | 14 | 7 | 4 | 56.0% | 32.0–78.6% |
| B03 · Thrust + staircase | 79 | 44 | 42 | 12 | 25 | 53.2% | 40.9–64.4% |
| B04 · T pullback/break | 295 | 67 | 149 | 46 | 100 | 50.5% | 44.1–56.8% |
| B05 · Stall/reclaim | 570 | 70 | 343 | 78 | 149 | 60.2% | 54.2–66.0% |
| B06 · Immediate breakout | 540 | 67 | 281 | 62 | 197 | 52.0% | 45.4–57.9% |
| B06 · Breakout/retest | 146 | 57 | 78 | 16 | 52 | 53.4% | 43.6–62.2% |
| B07 · Failed breakdown/reclaim | 154 | 60 | 80 | 30 | 44 | 51.9% | 42.4–61.6% |
| B08 · Band rebound, price | 60 | 40 | 28 | 11 | 21 | 46.7% | 33.3–60.0% |
| B08 · Band rebound + RSI | 9 | 9 | 5 | 3 | 1 | 55.6% | 20.0–88.9% |
| B09 · One-minute staircase | 1270 | 70 | 701 | 156 | 412 | 55.2% | 49.1–60.7% |
| B10 · Opening-range immediate | 57 | 57 | 35 | 10 | 11 | 61.4% | 49.0–73.8% |
| B10 · Opening-range retest | 12 | 12 | 7 | 2 | 3 | 58.3% | 28.6–87.5% |

There were no same-minute first-touch ties in these third-tranche strict-VT rows.
They would remain ambiguous and in the denominator if present. B06's neither
rate was36.5%, versus38.4% in tranche2; its adverse rate rose from8.7% to11.5%.
The third-tranche deterioration of the former favorites therefore cannot simply
be described as every rule facing a lower baseline than in tranche2: B01 and
B05 actually improved. No dealer-gamma or IV causal explanation was tested here.

## Repeated-entry sensitivities, third tranche

These are the same predeclared sensitivities, not newly optimized rules.

| Entry | All entries | First per day | At least60m apart |
| --- | --- | --- | --- |
| B01 · Fixed-time control | 199/337 · 59.1% | 50/75 · 66.7% | 199/337 · 59.1% |
| B02 · Five-minute thrust | 14/25 · 56.0% | 6/13 · 46.2% | 10/19 · 52.6% |
| B03 · Thrust + staircase | 42/79 · 53.2% | 20/44 · 45.5% | 31/63 · 49.2% |
| B04 · T pullback/break | 149/295 · 50.5% | 40/67 · 59.7% | 82/163 · 50.3% |
| B05 · Stall/reclaim | 343/570 · 60.2% | 44/70 · 62.9% | 118/204 · 57.8% |
| B06 · Immediate breakout | 281/540 · 52.0% | 38/67 · 56.7% | 98/183 · 53.6% |
| B06 · Breakout/retest | 78/146 · 53.4% | 32/57 · 56.1% | 53/95 · 55.8% |
| B07 · Failed breakdown/reclaim | 80/154 · 51.9% | 30/60 · 50.0% | 46/95 · 48.4% |
| B08 · Band rebound, price | 28/60 · 46.7% | 21/40 · 52.5% | 25/52 · 48.1% |
| B08 · Band rebound + RSI | 5/9 · 55.6% | 5/9 · 55.6% | 5/9 · 55.6% |
| B09 · One-minute staircase | 701/1270 · 55.2% | 41/70 · 58.6% | 122/222 · 55.0% |
| B10 · Opening-range immediate | 35/57 · 61.4% | 35/57 · 61.4% | 35/57 · 61.4% |
| B10 · Opening-range retest | 7/12 · 58.3% | 7/12 · 58.3% | 7/12 · 58.3% |

B06 first-per-day is38/67 (56.7%), while a60-minute cooldown is98/183 (53.6%).
Neither reproduces the original high hit rates. B01's first eligible daily entry
is50/75 (66.7%); time-of-day selection remains a competing explanation for apparent
first-entry improvements. These raw cross-rule rates are not controlled effects.

## What waiting for another condition retained and lost

The paired ledger preserves setups rather than deduplicated entry minutes.
B06 has150 eligible delayed setup records corresponding to146 distinct retest
minutes. On the same150 setups, immediate and retest each hit53.3%; waiting omits
201 successful immediate parents that never produce an eligible delayed entry.

B08 RSI retains9 of60 price-reentry setups. Five of those nine hit either way,
while23 successful price-only parents have no eligible RSI entry. Its55.6% rate
does not establish an independent improvement over those same retained setups.

B10 retest retains12 of57 immediate setups. On those same12, immediate hits5/12
and retest7/12;30 successful immediate parents do not produce a retest. That small
paired improvement is worth preserving as evidence, but is not confirmation of
the previously observed85% retest rate. Each delayed entry has its own60-minute
clock and entry price. These are not equal-start-time causal comparisons.

The inherited same-hour B01 contrasts remain in comparison.csv solely as timing
diagnostics. A later setup selects an earlier control partly using price movement
after the control's entry. Their confidence intervals do not fix this selection
issue, and they are not a promotion rule or proof of signal uplift.

## Complete coverage ledger and remaining exclusions

The180 excluded dates have these mutually exclusive recorded reason combinations:

| Reason combination | Dates |
| --- | --- |
| open_not_above_vt | 160 |
| missing_matching_preopen_note | 7 |
| missing_matching_preopen_note|open_not_above_vt | 3 |
| conflicting_preopen_vt | 3 |
| incomplete_spx | 3 |
| conflicting_preopen_vt|open_not_above_vt | 2 |
| missing_spx | 1 |
| missing_or_invalid_vt|missing_spx | 1 |

Above-recorded-VT dates that remain excluded are shown explicitly:

| Date | Recorded VT | 09:30 open | Reason |
| --- | --- | --- | --- |
| 2025-02-07 | 6045 | 6083.13 | missing_matching_preopen_note |
| 2025-06-06 | 5900 | 5987.06 | conflicting_preopen_vt |
| 2025-07-03 | 6170 | 6246.46 | incomplete_spx |
| 2025-07-07 | 6145 | 6259.04 | conflicting_preopen_vt |
| 2025-07-08 | 6220 | 6234.03 | conflicting_preopen_vt |
| 2025-09-22 | 6620 | 6654.28 | missing_matching_preopen_note |
| 2025-09-23 | 6620 | 6692.44 | missing_matching_preopen_note |
| 2025-09-24 | 6665 | 6669.79 | missing_matching_preopen_note |
| 2025-11-28 | 6785 | 6822.52 | incomplete_spx |
| 2025-12-22 | 6835 | 6865.21 | missing_matching_preopen_note |
| 2025-12-24 | 6895 | 6904.91 | incomplete_spx |
| 2026-04-08 | 6600 | 6754.36 | missing_matching_preopen_note |
| 2026-04-13 | 6785 | 6806.47 | missing_matching_preopen_note |

The matching preopen Feb7,2025 article has no extracted SPX VT table cell; Sep22–24
have no saved notes. Dec22,2025 and Apr13,2026 publication labels extend past the
open; Apr8,2026 has only an afternoon note. Jun6 and Jul7–8,2025 disagree with
the corrected CSV. These are specific evidence failures, not dates quietly
discarded because of outcomes. The three early-close dates have incomplete
full-session coverage under the frozen390-minute rule.

April7,2025 has four invalid native OHLC observations in the existing SDK response.
The response was reused and rejected; no bars were repaired. September17,2026 was
the single new ThetaData SDK request:391 raw observations,390 normalized RTH bars.
Its09:30 open7631.44 is below the observed preopen VT7660, so it fails eligibility.
Sep14–16 likewise open below their directly observed preopen-note VT values.
Those recent note-only dates extend the audit beyond the CSV's Sep11 endpoint,
without modifying the shared CSV or using next-day levels.

Third-tranche calendar coverage:

| Month | Dates |
| --- | --- |
| 2025-01 | 13 |
| 2025-03 | 3 |
| 2025-04 | 4 |
| 2025-05 | 17 |
| 2025-06 | 17 |
| 2025-07 | 19 |
| 2025-08 | 12 |
| 2025-09 | 2 |
| 2025-12 | 1 |
| 2026-04 | 1 |

This is a historical extension with a substantially different date mix, not a
randomly assigned experiment or guaranteed unseen holdout. The ten original
dashboard dates are shown separately in the full table; their presence in the
249-date descriptive total must not be confused with new evidence.

## Verification and storage

The experiment preserves the committed eight rule-module hashes and scoring
helpers. Input/source/protocol/analysis hashes and entry identities were frozen
before outcomes. The expanded chronological history contains999 source sessions,
with999 included in five-minute history and990 full sessions in minute-RSI history.
Partial history contributes only complete five-minute bins; nothing is filled.
No evaluated event has a prior100-bar calendar gap above four days.

Every prior7,465 raw setup identity and7,313 distinct opportunity reproduces,
including the762 strict-VT B06 subset. Every prior outcome and351 shared summary
rows reproduce exactly. The ten development dates separately reproduce all441
original dashboard identities. Three new-date temporal-prefix checks pass.

The independent verifier rereads native files and checks all12,284 distinct entry
prices, first-touch outcomes and causal VT gates across249 dates; all1,053 summary
rows reconcile. The raw setup ledger contains12,534 records; strict-VT primary
has9,320 distinct opportunities including3,554 in tranche3. Twenty-four targeted
publication, cohort, causal-scoring and accounting tests pass; Ruff passes. No
existing dashboard, rule snapshot, old study or raw source file was changed.

Data was reused wherever available. One new ThetaData index-history request;
zero option-history or ORATS requests. All new data and provenance reside under:

`/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1`

- [Full comparison table](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/comparison.csv):1,053 rows across3 VT scopes,3 sensitivities,9 cohort groups and13 variants.
- [All429 calendar dates and reasons](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/population.csv), [selected dates](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/selected_days.csv), [note extracts and timestamps](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/vt_note_provenance.json).
- [Third-tranche recovered versus legacy-eligible dates](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/third_admission_comparison.csv).
- [Every distinct event](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/distinct_event_outcomes.csv), [paired setups](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/paired_setup_comparison.csv), [independent checks](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/independent_verification.json).
- [Frozen protocol](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_third_tranche_2026-09-19/PROTOCOL.md), [publication logic](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_third_tranche_2026-09-19/provenance.py), [pipeline](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_third_tranche_2026-09-19/pipeline.py).

Stages are `pipeline.py audit`, `coverage`, `prepare`, `freeze`, `generate`,
`outcomes`, `analyze`, then `verify_results.py` and `report.py`. Existing artifacts
are immutable; deliberate reproduction requires a new namespace. Source metadata,
native hashes and schema inventory are registered in central CHANGELOG and
DATA_DICTIONARY with this isolated study's commit. Earlier notes remain preserved;
this report is the updated candidate assessment after tranche3.
