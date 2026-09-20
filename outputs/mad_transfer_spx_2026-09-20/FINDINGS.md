# Reviewed MAD transfers and SPX comparison — findings

Completed September 20, 2026. **January 2025–September 18, 2026; above-VT entries only.**
Target: **+5 before −10 within 60 native minute bars**, including entry. A later
reversal after +5 does not affect the result. Partial 2026 H2 is labeled throughout.

## CIO readout

**B09 accepting sector F4 OR SPX is the most promising opportunity expansion in
this bounded round:** 198/318 = 62.3%, compared with sector F4's 115/188 = 61.2%.
It adds 130 observed entries and 83 targets in the all-entry accounting. Active
dates increase from 95 to 121. With 60-minute spacing it gives 107/175 = 61.1%,
versus sector-only 76/121 = 62.8% and plain B09 285/554 = 51.4%. That is more
opportunities with a modest accuracy tradeoff under spacing, not an across-policy
improvement on the sector-only filter. First/day falls to 70/121 = 57.9%, versus
61/95 = 64.2% for sector F4. SPX alone is particularly sensitive to repeated
signals: 61.5% for all entries, 56.1% spaced, and 48.1% first/day.

**B05 + F4 partly worked as a transfer:** 70/112 = 62.5% versus its parent's 55.6%,
and 65/100 = 65.0% with spacing. Its same-date/hour contrast is also favorable.
However, the improvement is concentrated in blocks that also have a qualifying
B09 signal. Without one, B05 + F4 is 37/70 = 52.9%, versus 53.4% for B05 in those
blocks. This supports a shared favorable market context more than a demonstrated
independent source of extra opportunities. B05 does not exceed B09 F4's retained
events, dates or spaced N. No combined-parent portfolio was tested.

**B07 is underpowered/uninformative for this decision:** F4 reaches 14/21 = 66.7%,
but only 20 dates and 4, 8, 7, 2 events across the four halves. Its uplift interval
is very wide and crosses zero. Without a corresponding B09 qualifying block,
it is 6/12 = 50.0%. S4 is only 19/32 = 59.4%. These samples cannot establish a
reliable transfer or rule out a real effect.

**The broad sign controls show little pooled all-entry benefit:** their changes
range from −2.3 to +0.2 percentage points. This says the
specific stricter rules look different from broad direction filters on these
dates. It does not isolate the value of MAD normalization from selectivity,
date/hour selection, or the previous research search.

## Fixed rule definitions and studied population

S4 requires at least four of the fixed eleven sectors with M>1. F4 requires at
least four sectors each with M>1 **and** b2<−1e−12. b2 is the IV slope in the latest
15-minute half. M=−a/(1.4826×historical MAD), a=(b2−b1)/15. IV may still be rising
under S4 if that rise is slowing sharply. F4 adds that it is already falling.
SPX uses exactly M>1 and b2<−1e−12 on native SPXW 30-day ATM IV. OR means accept
the B09 entry if either sector F4 or SPX qualifies; neither threshold was tuned.

The original price triggers, measurement/recovery guards, and 60-prior-session
scales are unchanged. Every entry uses T−1; every source lies in T−30…T−1.
History is strictly prior. Calibration/diagnostic hour blocks are anchored at
09:30 (09:30–10:29, etc.), not whole clock hours. Prior native RTH lows and entry
open must be strictly above same-day VT. No future all-day condition was used.

There are 239 research dates, including zero-entry dates, and 5,093 distinct
parent entries: B09 3,141, B07 415, B05 1,537. The 10 development dates are excluded.
The SPX measurement backfill includes 2024; the sector-matched outcome experiment
does not. Earlier results from a full 2024–2026 population are not its baselines.

| Parent | Rule | Target first / N | Active dates |
| --- | --- | --- | --- |
| B09 | Plain parent | 1704/3141 = 54.3% | 178 |
| B09 | S4: acceleration | 139/235 = 59.1% | 100 |
| B09 | F4: acceleration + falling | 115/188 = 61.2% | 95 |
| B07 | Plain parent | 233/415 = 56.1% | 159 |
| B07 | S4: acceleration | 19/32 = 59.4% | 29 |
| B07 | F4: acceleration + falling | 14/21 = 66.7% | 20 |
| B05 | Plain parent | 854/1537 = 55.6% | 182 |
| B05 | S4: acceleration | 91/149 = 61.1% | 98 |
| B05 | F4: acceleration + falling | 70/112 = 62.5% | 81 |
| B09 | SPX falling MAD | 115/187 = 61.5% | 79 |
| B09 | Sector F4 OR SPX | 198/318 = 62.3% | 121 |

## Every half-year

| Parent | Rule | 2025 H1 | 2025 H2 | 2026 H1 | 2026 H2 partial |
| --- | --- | --- | --- | --- | --- |
| B09 | Plain parent | 496/897 = 55.3% | 587/1215 = 48.3% | 514/858 = 59.9% | 107/171 = 62.6% |
| B09 | S4: acceleration | 45/78 = 57.7% | 51/89 = 57.3% | 38/58 = 65.5% | 5/10 = 50.0% |
| B09 | F4: acceleration + falling | 37/61 = 60.7% | 39/69 = 56.5% | 35/51 = 68.6% | 4/7 = 57.1% |
| B07 | Plain parent | 69/121 = 57.0% | 75/155 = 48.4% | 66/105 = 62.9% | 23/34 = 67.6% |
| B07 | S4: acceleration | 3/6 = 50.0% | 8/12 = 66.7% | 5/10 = 50.0% | 3/4 = 75.0% |
| B07 | F4: acceleration + falling | 2/4 = 50.0% | 7/8 = 87.5% | 4/7 = 57.1% | 1/2 = 50.0% |
| B05 | Plain parent | 246/420 = 58.6% | 297/565 = 52.6% | 265/447 = 59.3% | 46/105 = 43.8% |
| B05 | S4: acceleration | 30/47 = 63.8% | 29/48 = 60.4% | 26/40 = 65.0% | 6/14 = 42.9% |
| B05 | F4: acceleration + falling | 23/36 = 63.9% | 20/33 = 60.6% | 22/32 = 68.8% | 5/11 = 45.5% |
| B09 | SPX falling MAD | 32/57 = 56.1% | 58/91 = 63.7% | 17/27 = 63.0% | 8/12 = 66.7% |
| B09 | Sector F4 OR SPX | 58/96 = 60.4% | 78/130 = 60.0% | 50/74 = 67.6% | 12/18 = 66.7% |

Both B05 magnitude rules have positive observed uplift in the three completed
halves. Neither B07 rule does. Those are descriptive patterns, not pass/fail
validation tests. B09 OR has a positive observed comparison in every half, but
partial H2 has only 18 qualifying entries. The *incremental* SPX-positive,
sector-negative subgroup does not improve in every completed half; see below.

## Repeated signals and the opportunity tradeoff

| Parent | Rule | All entries | First qualifying/day | 60-minute spacing |
| --- | --- | --- | --- | --- |
| B09 | Plain parent | 1704/3141 = 54.3% | 97/178 = 54.5% | 285/554 = 51.4% |
| B09 | S4: acceleration | 139/235 = 59.1% | 60/100 = 60.0% | 84/142 = 59.2% |
| B09 | F4: acceleration + falling | 115/188 = 61.2% | 61/95 = 64.2% | 76/121 = 62.8% |
| B07 | Plain parent | 233/415 = 56.1% | 87/159 = 54.7% | 138/253 = 54.5% |
| B07 | S4: acceleration | 19/32 = 59.4% | 17/29 = 58.6% | 18/30 = 60.0% |
| B07 | F4: acceleration + falling | 14/21 = 66.7% | 13/20 = 65.0% | 14/21 = 66.7% |
| B05 | Plain parent | 854/1537 = 55.6% | 104/182 = 57.1% | 295/544 = 54.2% |
| B05 | S4: acceleration | 91/149 = 61.1% | 61/98 = 62.2% | 81/130 = 62.3% |
| B05 | F4: acceleration + falling | 70/112 = 62.5% | 54/81 = 66.7% | 65/100 = 65.0% |
| B09 | SPX falling MAD | 115/187 = 61.5% | 38/79 = 48.1% | 60/107 = 56.1% |
| B09 | Sector F4 OR SPX | 198/318 = 62.3% | 70/121 = 57.9% | 107/175 = 61.1% |

Filter before thinning; each parent/rule/cohort has its own chronological policy.
Spacing resets daily and never depends on outcomes. A union can change which
entry is first or which later entries survive spacing. Therefore the 130 raw
additions cannot be added to the spaced/first-day counts as if nothing else changes.
Different parents and execution-policy cohorts must not be summed as independent
trades. The all-entry OR retains 198/1704 = 11.6% of plain B09 targets and excludes
1,506; it expands the selective IV subset, not the unfiltered parent.

## SPX disagreement: what actually supplied the extra entries

SPX scores were available for **all 3,141 B09 entries**, even though three dates
have gaps somewhere in the full SPX measurement history. Before outcomes were
joined, SPX qualified on 187 (6.0%) and OR on 318 (10.1%). That participation was
measured, not inferred from a normal distribution or selected to match sector N.

| Sector F4 | SPX | Target first / N | Dates |
| --- | --- | --- | --- |
| yes | yes | 32/57 = 56.1% | 36 |
| yes | no | 83/131 = 63.4% | 81 |
| yes | unknown | 0/0 · unestimable | 0 |
| no | yes | 72/109 = 66.1% | 59 |
| no | no | 1406/2661 = 52.8% | 176 |
| no | unknown | 0/0 · unestimable | 0 |
| unknown | yes | 11/21 = 52.4% | 15 |
| unknown | no | 100/162 = 61.7% | 59 |
| unknown | unknown | 0/0 · unestimable | 0 |

The useful-looking subgroup is **SPX yes / sector definite no: 72/109 = 66.1%**,
versus 1406/2661 = 52.8% when both definitely fail. Its all-entry date-bootstrap
difference is +13.2 percentage points, with an unadjusted interval of +1.6 to
+24.2. With spacing it is 45/73 = 61.6% and the difference interval crosses zero;
first/day it is 34/59 = 57.6%, slightly below the corresponding negative group.

By half the incremental group is 19/31 = 61.3%, 37/54 = 68.5%, 8/14 = 57.1%, and
8/10 = 80.0%. In 2026 H1 it is below the jointly measurable sector-negative
benchmark of 415/707 = 58.7%. Its strongest evidence comes from 2025 H2; the small
2026 groups cannot establish stable incremental value.

The additional **sector-unknown / SPX-yes** entries are 11/21 = 52.4%. Report them
as coverage recovery, separately from the 109 definite disagreements. OR leaves
162 unresolved sector-unknown/SPX-no entries, with 100 targets (61.7%); unresolved
does not mean these were failures. No unknown vote was imputed.

On the common measurable parent, there are 2,958 entries at 53.9%. F4 retains
115/188 = 61.2%; SPX 104/166 = 62.7%; OR 187/297 = 63.0%. This removes the
sector-unknown additions from the accuracy comparison. All nine state combinations
and common/full/all-eleven comparisons are in the data tables.

Requiring **both** confirmations would leave 32/57 = 56.1%, compared with 83/131 =
63.4% for sector yes / SPX no. Agreement is not the winner in these data. This is
the predeclared cross-table diagnosis, not a new fitted AND strategy.

## Date/hour selection and overlap

The same-selected-date comparison restricts the parent to dates on which the
rule qualifies. The within-date/block comparison uses only strata containing
both qualifiers and definite nonqualifiers, then weights blocks equally within
date and dates equally. These are distinct descriptive comparisons; neither is
a causal treatment effect.

| Parent | Rule | Same-date parent delta pp | Within-block delta pp | 95% interval pp | Matched yes/no events | Dates | Kept/all strata |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B09 | S4: acceleration | +0.19 | +2.23 | -5.1 to +9.6 | 228/671 | 96 | 154/647 |
| B09 | F4: acceleration + falling | +2.08 | +2.95 | -4.4 to +10.5 | 183/572 | 91 | 130/647 |
| B07 | S4: acceleration | +2.08 | -9.09 | -41.7 to +25.0 | 11/17 | 11 | 11/285 |
| B07 | F4: acceleration + falling | +5.24 | +10.00 | -25.0 to +46.2 | 10/15 | 10 | 10/285 |
| B05 | S4: acceleration | +5.23 | +7.49 | -3.3 to +18.7 | 126/219 | 89 | 117/649 |
| B05 | F4: acceleration + falling | +7.84 | +14.04 | +2.9 to +26.1 | 98/181 | 73 | 91/649 |
| B09 | SPX falling MAD | +3.67 | +0.47 | -8.8 to +9.7 | 181/512 | 77 | 120/647 |
| B09 | Sector F4 OR SPX | +4.72 | +2.88 | -3.6 to +9.4 | 304/806 | 117 | 195/647 |

B09 OR's +8.0-point full-parent contrast becomes +4.7 versus the parent on its
selected dates, then +2.9 within matched date/hour blocks, with the latter interval
crossing zero. SPX alone has only +0.5 within those blocks. Thus the full-sample
advantage cannot yet be separated convincingly from selecting favorable times.
B05 F4 has the stronger within-block contrast (+14.0, interval +3.0 to +26.1),
but its full-parent uncertainty remains wide and the shared-B09 diagnostic matters.

| Parent | Rule | With B09 block | Without B09 block | Parent without B09 block | Exact-minute overlap |
| --- | --- | --- | --- | --- | --- |
| B07 | S4 | 8/9 = 88.9% | 11/23 = 47.8% | 194/360 = 53.9% | 4/4 = 100.0% |
| B07 | F4 | 8/9 = 88.9% | 6/12 = 50.0% | 198/368 = 53.8% | 4/4 = 100.0% |
| B05 | S4 | 40/53 = 75.5% | 51/96 = 53.1% | 683/1290 = 52.9% | 7/10 = 70.0% |
| B05 | F4 | 33/42 = 78.6% | 37/70 = 52.9% | 706/1323 = 53.4% | 6/7 = 85.7% |

These block labels look across the whole date/hour block, potentially including
a B09 signal later than the transfer entry. They are **retrospective overlap
diagnostics, not available-at-entry trading gates**. Removing an overlapping
block does not create out-of-sample data; all dates have been used before.
Shared price outcomes and IV windows limit claims that the transfers are new
independent opportunities.

## Broad sign controls

| Parent | Plain | a<0 in four | a<0 + falling in four | S4 | F4 |
| --- | --- | --- | --- | --- | --- |
| B09 | 1704/3141 = 54.3% | 1378/2544 = 54.2% | 1046/1933 = 54.1% | 139/235 = 59.1% | 115/188 = 61.2% |
| B07 | 233/415 = 56.1% | 166/306 = 54.2% | 104/193 = 53.9% | 19/32 = 59.4% | 14/21 = 66.7% |
| B05 | 854/1537 = 55.6% | 681/1221 = 55.8% | 487/875 = 55.7% | 91/149 = 61.1% | 70/112 = 62.5% |

The B09 controls reproduce the reviewer-disclosed 2,544 and 1,933 qualifiers
exactly. They were already inspected before this execution. Some thinned-policy
control comparisons improve, particularly B05; all policies are published in
ALL_RESULTS.md. The broad controls are much less selective, so this is not a
matched-retention test and cannot establish a benefit caused by normalization.
No raw-magnitude threshold or retention-matching sweep was added.

## Coverage held constant and gap causes

| Parent | Half | Entries | All 11 observed | All-11 share | Mean valid sectors |
| --- | --- | --- | --- | --- | --- |
| B09 | 2025_H1 | 897 | 593 | 66.1% | 10.52 |
| B09 | 2025_H2 | 1215 | 823 | 67.7% | 10.65 |
| B09 | 2026_H1 | 858 | 277 | 32.3% | 10.12 |
| B09 | 2026_H2 | 171 | 95 | 55.6% | 10.56 |
| B07 | 2025_H1 | 121 | 80 | 66.1% | 10.50 |
| B07 | 2025_H2 | 155 | 96 | 61.9% | 10.54 |
| B07 | 2026_H1 | 105 | 39 | 37.1% | 10.27 |
| B07 | 2026_H2 | 34 | 22 | 64.7% | 10.65 |
| B05 | 2025_H1 | 420 | 265 | 63.1% | 10.47 |
| B05 | 2025_H2 | 565 | 338 | 59.8% | 10.57 |
| B05 | 2026_H1 | 447 | 181 | 40.5% | 10.27 |
| B05 | 2026_H2 | 105 | 66 | 62.9% | 10.63 |

The all-eleven sensitivity uses the same eleven sectors and thresholds, with
the corresponding restricted parent. It changes the date/time population and
does not cure nonrandom missingness outside that population.

| Parent | Rule | All-eleven result | Restricted parent |
| --- | --- | --- | --- |
| B09 | S4: acceleration | 92/157 = 58.6% | 908/1788 = 50.8% |
| B09 | F4: acceleration + falling | 73/118 = 61.9% | 908/1788 = 50.8% |
| B07 | S4: acceleration | 10/19 = 52.6% | 125/237 = 52.7% |
| B07 | F4: acceleration + falling | 8/13 = 61.5% | 125/237 = 52.7% |
| B05 | S4: acceleration | 58/96 = 60.4% | 455/850 = 53.5% |
| B05 | F4: acceleration + falling | 44/69 = 63.8% | 455/850 = 53.5% |
| B09 | SPX falling MAD | 63/99 = 63.6% | 908/1788 = 50.8% |
| B09 | Sector F4 OR SPX | 112/180 = 62.2% | 908/1788 = 50.8% |

The main direction of the B05 F4 and B09 OR comparisons remains favorable here,
but sample sizes fall. B07 S4 becomes 10/19 = 52.6%, essentially its restricted
parent's 52.7%; F4 has only 13 events. Per-half/block valid counts, instrument
coverage, state counts and all unknown outcomes are saved, not suppressed.

| ETF | Recorded gap cause | Missing ETF-entry slots |
| --- | --- | --- |
| XLB | captured_but_current_window_rejected | 46 |
| XLB | no_allowed_expiry_bracket | 197 |
| XLC | captured_but_current_window_rejected | 180 |
| XLF | captured_but_current_window_rejected | 35 |
| XLP | captured_but_current_window_rejected | 45 |
| XLRE | captured_but_current_window_rejected | 831 |
| XLRE | no_allowed_expiry_bracket | 1220 |
| XLU | captured_but_current_window_rejected | 163 |
| XLY | captured_but_current_window_rejected | 25 |

There are 2,742 missing ETF-entry slots across the three parents, representing
2,630 distinct ETF/date/endpoints because parents can share observations. Of
these, 1,417 are missing permitted expiry brackets and 1,325 are captured days
with a rejected current window. XLRE contributes 2,051 slots (1,220 bracket,
831 current-window). Every cause is reconciled to the unchanged collection
receipt and source-support table in gap_source_support.csv. Source rejection
is not a claim that the market had no quote; strike coverage and quote guards
are distinct from absent listed expiries. No refetch, guard relaxation, added
expiry, imputation, or selective repair was performed.

## Descriptive uncertainty and limitations

| Parent | Rule | Observed uplift pp | 95% uplift interval pp | 95% hit-rate interval |
| --- | --- | --- | --- | --- |
| B09 | S4: acceleration | +4.90 | -1.5 to +11.2 | 51.9–66.1% |
| B09 | F4: acceleration + falling | +6.92 | +0.3 to +13.4 | 53.6–68.2% |
| B07 | S4: acceleration | +3.23 | -13.8 to +20.3 | 41.7–77.3% |
| B07 | F4: acceleration + falling | +10.52 | -10.4 to +30.3 | 44.4–87.1% |
| B05 | S4: acceleration | +5.51 | -1.8 to +13.3 | 53.1–69.5% |
| B05 | F4: acceleration + falling | +6.94 | -2.2 to +16.6 | 52.7–72.9% |
| B09 | SPX falling MAD | +7.25 | -1.4 to +15.5 | 52.2–70.4% |
| B09 | Sector F4 OR SPX | +8.01 | +2.5 to +13.2 | 55.6–68.4% |

Intervals use 5,000 shared whole-date resamples across the 239 selected research
dates, seed 20260920. This new seed means Monte Carlo bounds for the unchanged
B09 references differ slightly from the original seed-20260919 report; no source
or point estimate changed. All modes and restricted-parent/sign-control
comparisons are in uncertainty.csv. Matched-block intervals resample dates with
equal-date weighting. These intervals do not adjust for earlier 105-rule/48-cell
searches, serial dependence across dates, or selection of these parent candidates.
All-eleven/overlap sensitivities are correlated checks, not independent replications.

Wide/sparse comparisons are underpowered or uninformative; zero-entry cells are
unestimable. No universal post-hoc N floor, significance score, threshold change,
or declaration of a validated/stable/deployable strategy is made. The results
support keeping B09 OR and B05 F4 as fixed exploratory candidates, with the
policy and overlap qualifications above. They do not justify another sweep.

## Complete outcome accounting

| Parent | Rule | N | +5 first | −10 first | Neither | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- |
| B09 | Plain parent | 3141 | 1704 | 685 | 751 | 1 |
| B09 | S4: acceleration | 235 | 139 | 61 | 35 | 0 |
| B09 | F4: acceleration + falling | 188 | 115 | 46 | 27 | 0 |
| B07 | Plain parent | 415 | 233 | 112 | 70 | 0 |
| B07 | S4: acceleration | 32 | 19 | 13 | 0 | 0 |
| B07 | F4: acceleration + falling | 21 | 14 | 7 | 0 | 0 |
| B05 | Plain parent | 1537 | 854 | 405 | 278 | 0 |
| B05 | S4: acceleration | 149 | 91 | 50 | 8 | 0 |
| B05 | F4: acceleration + falling | 112 | 70 | 37 | 5 | 0 |
| B09 | SPX falling MAD | 187 | 115 | 51 | 21 | 0 |
| B09 | Sector F4 OR SPX | 318 | 198 | 77 | 43 | 0 |

Higher target rate does not imply a lower adverse-first share: for example B05
F4 has 37 adverse outcomes among 112 versus 405 among 1,537 in its parent. The
user's first+5 objective is retained; no linear-payout expectancy or posttarget
giveback score was substituted.

## Verification, artifacts and review status

Ten boundary tests and Ruff pass. Local scalar replay reproduced all
26,654 memberships and 2,592
summary rows. Direct native-price scans verified all 5,093
entries, their strictly causal VT eligibility and first-touch outcomes. All 36
inherited half/policy parent baselines, previous B09 S4/F4 memberships, reviewer
sign controls, 204 within-block rows, and 324 SPX cross rows reconcile. Source
hashes, prior-history date ledgers, score arithmetic and source windows passed.

The external strategy review and conditional recheck were supplied and their
accepted requirements implemented. The new execution has **local verification,
not a new independent Claude code/results sign-off**. The final author amendments
after the recheck remain identified in the supplied review response.

- [Frozen execution protocol](/Users/dgrissen/Dev/delta_bomb/outputs/mad_transfer_spx_2026-09-20/PROTOCOL.md)
- [Every fixed rule, policy and half-year](/Users/dgrissen/Dev/delta_bomb/outputs/mad_transfer_spx_2026-09-20/ALL_RESULTS.md)
- [Entry classifications and input/code hashes](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/freeze.json)
- [Full summary, unknowns and selected-date comparisons](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/summary.csv)
- [Uncertainty](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/uncertainty.csv)
- [Within-date/hour support and estimates](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/within_date_block.csv)
- [B09 overlap groups](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/b09_overlap.csv)
- [SPX disagreement groups](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/spx_cross.csv)
- [Incremental SPX groups](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/spx_incremental.csv)
- [Per-entry gap source support](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/gap_source_support.csv)
- [Verification receipt](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/verification.json)
- [Data dictionary](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/DATA_DICTIONARY.md)

![Fixed-rule results by half-year](/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1/half_year_results.png)
