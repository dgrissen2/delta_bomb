# Previous sector-IV rules on the full 2024–2026 above-VT study

**Completed numerical comparison. Independent Claude review: CONDITIONAL PASS;
findings, repairs and remaining interpretation limits are documented below.**
Score throughout: **SPX reaches +5 before −10 within sixty native minute bars**.
Price action after reaching +5 does not change a winner.

## CIO interpretation

The original broad falling-IV and acceleration filters do not improve B06 on the
expanded population. B06 produces 1,208 winners in 2,382 entries, or 50.7%.
Requiring falling IV produces 729/1,454, or 50.1%; requiring downward acceleration
as well produces 315/632, or 49.8%. We remove most opportunities without gaining
accuracy. Recovering midpoint IV when bid IV fails increases measurement coverage,
but does not restore the early pilot's B06 advantage.

**B07 failed breakdown/range reclaim is the clearest simpler transfer lead.**
Adding the original six-sector acceleration condition raises its observed rate
from 393/769 (51.1%) to 96/157 (61.1%), with a higher percentage in all six halves
and in the first-per-day and spaced comparisons. Midpoint recovery gives 100/163
(61.3%). This is still a selective subset of a different price recipe, but it
deserves attention alongside the B09 opportunity-count experiment.

The strongest opportunity-count lead is **B09's one-minute staircase with falling
and accelerating IV in eight sectors under the quote guards**. The 100% quote-width
guard retains 69/105 winners (65.7%); the 50% guard retains 44/66 (66.7%). Adding
these entries to thrust gives **128/197 (65.0%)** and **103/158 (65.2%)**, respectively,
against thrust's 59/92 (64.1%). These are promising transfers to a different price
setup. They do not rescue the original B06 result, and the 50% subset supplies only
39 distinct B09 dates. Both thresholds were already in the frozen inventory.

Opening-range breakouts offer a secondary, smaller N experiment. The original
acceleration rule adds 25 entries and 16 winners, leaving
the combined hit rate essentially unchanged at 75/117, or 64.1%. Midpoint recovery
adds 28 entries and 18 winners: 77/120, or 64.2%, versus thrust's 59/92, or 64.1%.
A guarded version adds 14 entries and 10 winners, giving 69/106, or 65.1%. Those
are possible ways to add opportunities, with a small amount of incremental evidence.
They do not establish that we can keep the higher percentage outside these dates.

## Exactly what was collected

All 421 selected dates were checked for every one of the eleven sector ETFs.
There are **411 research dates and ten separately reported development dates**.
The underlying price study audited 681 completed sessions through September 18,
2026, and selected dates under its existing provenance, session-coverage and VT
rules. This is the entire selected study population, not every calendar date.

For 2024, all **172 dates × 11 ETFs = 1,892 sector-days** are accounted for:
**1,816 captured and 76 without an allowed expiry bracket**, with no downloads
pending. The expiry gaps are 43 XLRE sector-days and 33 XLB sector-days. Across
all three years and both cohorts there are 4,488 captured sector-days and 143
expiry gaps. A captured day can still contain unusable minute quotes.

| Half-year | Captured sector-days | No allowed expiry bracket |
|---|---:|---:|
| 2024 H1 | 925 | 32 |
| 2024 H2 | 891 | 44 |
| 2025 H1 | 659 | 23 |
| 2025 H2 | 991 | 21 |
| 2026 H1 | 721 | 16 |
| 2026 H2, including the ten development dates | 301 | 7 |

All new native and derived data are under
`/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1/`.
The acquisition used the ThetaData Python SDK and one-minute implied-volatility
and first-order-Greeks endpoints. There were 5,293 logged new data requests, all
successful; existing exact-parameter caches were reused by hash. The combined
input audit covers 16,300 distinct native endpoint files. No new MAD history or
MAD-based outcome filter is part of this run.

Historical capitalization weighting uses the preceding session's IVV equity
holdings as a proxy. Of 421 dated snapshots, 404 passed the unchanged validator;
17 response bodies were retrieved but rejected. Their weighted rules remain
unknown. Revalidating these existing bodies fetched nothing and did not change
accepted weights. Exact historical publication/revision timing is uncertified,
so these weighted comparisons are a proxy sensitivity.

## The frozen calculation

The universe is XLC, XLY, XLP, XLE, XLF, XLV, XLI, XLB, XLRE, XLK and XLU.
Each coordinate targets thirty calendar days to expiry using the nearest listed
bracket within 8–65 DTE, or an exact thirty-day expiry. There is no extrapolation.
The surface coordinates are ATM at spot and native ±25-delta wings. Strike/delta
interpolation operates in variance; expiry interpolation uses total variance.
The midpoint `implied_vol` is the signal value. Bid/ask IV supplies validity and
measurement envelopes, not an alternative bid-IV directional signal.

For entry minute T, the original reference consists of the thirty observations
T−35 through T−6. Fit an OLS slope to each fifteen-observation half:

`b1 = sum((i−7) × IV[i]) / 280`, for i=0…14;
`b2` uses the same coefficients on observations 15…29;
`a = (b2−b1) / 15`.

IV is expressed in percentage points, slopes in points/minute, and acceleration
in points/minute². Falling means b2 < −1e−12. Falling with downward acceleration
requires both b2 and a < −1e−12 in the same sector. The original policies require
all thirty observations. Six- and eight-sector versions are separate fixed rules.
This window was inherited from B06; applying it to other entries is a transfer
hypothesis. Entries before 10:05 cannot have this full same-session reference.

Unknowns always preserve the eleven-sector denominator. Six observed qualifiers
are enough for yes. If observed qualifiers plus all missing sectors cannot reach
six, the state is no. Otherwise it is unknown. Unknown is not a nonqualifier.
Missing expiries, rejected quotes and rejected weights never become negative IV
readings or cause the remaining sectors to be renormalized.

Four prior quote policies remain separate: original validity; recovery when bid
IV fails but the other midpoint/quote requirements hold; and guarded recovery
with relative quote-width limits of 100% or 50% plus the inherited prior-minute
checks. Positive dollar bids remain mandatory. Guards apply to the selected
surface constituents, and can exclude observations that the original policy
accepted. The guarded rules can therefore have more unknowns than the original.
Permitting additional valid midpoint observations can also change the interpolation
and classification, not merely fill otherwise empty windows.

Balanced recovery is an explicitly labeled measurement transfer. It takes strict
exact observations first, then strict observations within two minutes in the same
hour block and reference window, then guarded-100 exact recovery. Actual source
timestamps are deduplicated, and the two slopes use actual elapsed times. It uses
no historical MAD normalization in this comparison.

## What the principal rules did

| Entry family and rule | Winners / N | Hit rate |
|---|---:|---:|
| Plain B06 channel breakout | 1,208 / 2,382 | 50.7% |
| B06: falling IV in six sectors | 729 / 1,454 | 50.1% |
| B06: falling and accelerating in six | 315 / 632 | 49.8% |
| B06: midpoint recovery, falling and accelerating | 341 / 678 | 50.3% |
| B06: guarded-100 recovery, falling and accelerating | 204 / 388 | 52.6% |
| B06: balanced recovery, falling and accelerating | 328 / 655 | 50.1% |
| B06: price rising and IV falling in the same six sectors | 409 / 801 | 51.1% |
| B06: price-only six-sector participation | 877 / 1,695 | 51.7% |
| Plain B07 failed breakdown/range reclaim | 393 / 769 | 51.1% |
| B07: original falling and accelerating in six | 96 / 157 | 61.1% |
| B07: midpoint recovery, falling and accelerating in six | 100 / 163 | 61.3% |
| B07: guarded-50, majority-weight falling and accelerating | 68 / 104 | 65.4% |
| Plain B09 one-minute staircase | 2,890 / 5,560 | 52.0% |
| B09: midpoint recovery, falling and accelerating | 734 / 1,361 | 53.9% |
| B09: guarded-100 recovery, falling and accelerating | 378 / 690 | 54.8% |
| B09: original falling and accelerating in eight sectors | 123 / 213 | 57.7% |
| B09: midpoint recovery, falling and accelerating in eight | 141 / 240 | 58.8% |
| B09: guarded-100 recovery, falling and accelerating in eight | 69 / 105 | 65.7% |
| B09: guarded-50 recovery, falling and accelerating in eight | 44 / 66 | 66.7% |
| Plain B03 existing thrust/staircase combination | 180 / 317 | 56.8% |
| B03: original falling and accelerating | 56 / 95 | 58.9% |
| B03: guarded-100 recovery, falling and accelerating | 33 / 52 | 63.5% |
| Plain B10 opening-range immediate breakout | 145 / 260 | 55.8% |
| B10: original falling and accelerating | 20 / 30 | 66.7% |
| B10: midpoint recovery, falling and accelerating | 23 / 34 | 67.6% |
| B10: guarded-100 recovery, falling and accelerating | 13 / 17 | 76.5% |

The 76.5% cell is only seventeen entries. It is a small exploratory lead, not the
winner of a reliable strategy selection exercise. For B09, 53.9% retains only
734 of 2,890 existing successes. The higher percentage has to justify losing
2,156 successes; its larger raw N does not erase that tradeoff.

B06's original acceleration yes and definite-no groups are almost identical:
315/632 versus 690/1,385, both about 49.8%. Unknowns achieved 203/365, or 55.6%.
The guarded-100 qualifier's 52.6% compares with 50.1% for its definite-no group
and 50.9% across its measurable cohort. Its 1,189 unknown B06 entries must remain
visible. A quality-policy change is not evidence that acceleration suddenly became
a strong independent signal.

Capitalization weighting does not repair B06: original weighted falling achieves
741/1,465, or 50.6%; weighted acceleration achieves 425/867, or 49.0%. Requiring
falling IV during the breakout as well as the earlier reference achieves 442/906,
or 48.8%. Pairing each sector's price rise with its own IV decline produces 51.1%,
versus 51.7% for the price-only breadth control. These operational filters do not
support the early attractive B06 narrative on the full population.

| Half-year | Plain B06 | B06 falling IV in six | B06 falling and accelerating in six |
|---|---:|---:|---:|
| 2024 H1 | 260/555 = 46.8% | 151/325 = 46.5% | 62/144 = 43.1% |
| 2024 H2 | 263/525 = 50.1% | 156/306 = 51.0% | 66/139 = 47.5% |
| 2025 H1 | 201/385 = 52.2% | 128/249 = 51.4% | 56/106 = 52.8% |
| 2025 H2 | 216/467 = 46.3% | 142/323 = 44.0% | 67/143 = 46.9% |
| 2026 H1 | 207/362 = 57.2% | 121/205 = 59.0% | 52/81 = 64.2% |
| 2026 H2 through September 18 | 61/88 = 69.3% | 31/46 = 67.4% | 12/19 = 63.2% |

The original acceleration rule looks helpful in 2026 H1 and weaker in both 2024
halves. Even excluding 2024, the expanded 2025–2026 acceleration result is only
187/349 (53.6%) against plain B06's 685/1,302 (52.6%). The deterioration is therefore
not simply a story about adding 2024. The early promising period did not generalize
strongly across the larger set of dates under this score.

## The comparable-price question has a narrower remaining hint

Matching fixes the rising-sector count and permits at most ten basis points of
difference in median signed sector return. It maximizes the number of one-to-one
pairs, then minimizes the return gap, without reusing entries. The pairs were
frozen before outcomes were attached. Global and within-half matching are shown
separately; matching does not control every aspect of timing or market context.

| B06 condition | Matching scope | Pairs | IV yes | Definite no |
|---|---|---:|---:|---:|
| Falling IV | Global | 432 | 208/432 = 48.1% | 201/432 = 46.5% |
| Falling IV | Within half-year | 421 | 223/421 = 53.0% | 194/421 = 46.1% |
| Falling and accelerating | Global | 509 | 256/509 = 50.3% | 247/509 = 48.5% |
| Falling and accelerating | Within half-year | 497 | 252/497 = 50.7% | 247/497 = 49.7% |
| Midpoint-recovered acceleration | Within half-year | 533 | 270/533 = 50.7% | 264/533 = 49.5% |
| Same-sector price/IV pairing | Within half-year | 286 | 150/286 = 52.4% | 134/286 = 46.9% |

Falling IV has a 6.9-point difference in the within-half matched subset, but only
1.6 points with global matching. The acceleration advantage is about one point
within halves. The matched-subset falling-IV result remains a conditional lead;
it has not supplied an executable broad filter that improves the full B06 pool.
Its sensitivity to which entries can be matched matters. These are descriptive
matched counts, not independent-pair significance tests or causal estimates.

## B07: the simpler transfer that repeated across half-years

For failed breakdown/range reclaim, original six-sector acceleration qualifies on
121 distinct dates. Its 96/157 (61.1%) compares with 254/539 (47.1%) for definite
nonqualifiers and 350/696 (50.3%) for the measurable cohort. Unknowns are 43/73
(58.9%); excluding them is a real opportunity cost. This is a stronger conditional
separation than the same rule produced for B06.

| Half-year | Plain B07 | Original six-sector acceleration B07 (dates) |
|---|---:|---:|
| 2024 H1 | 87/203 = 42.9% | 21/34 = 61.8% (23) |
| 2024 H2 | 73/151 = 48.3% | 18/32 = 56.3% (27) |
| 2025 H1 | 69/121 = 57.0% | 14/22 = 63.6% (17) |
| 2025 H2 | 75/155 = 48.4% | 22/41 = 53.7% (30) |
| 2026 H1 | 66/105 = 62.9% | 17/23 = 73.9% (19) |
| 2026 H2 through September 18 | 23/34 = 67.6% | 4/5 = 80.0% (5) |

First-per-day original-acceleration B07 is 72/121 (59.5%), versus the unfiltered
141/283 (49.8%). Sixty-minute spacing is 82/137 (59.9%), versus 239/470 (50.9%).
The all-entry 95% date-bootstrap interval is 53.1–69.1%; the difference from all
B07 entries is +3.4 to +16.7 percentage points before any multiple-testing adjustment.
The observed advantage survives these descriptive checks, but the late-half cells
remain small and the family transfer was one of many comparisons.

The stricter weighted alternative reaches 68/104 (65.4%), on 77 dates, versus
147/302 (48.7%) for definite nonqualifiers and 215/406 (53.0%) across measurable
entries. It has 363 unknowns and inherits the historical IVV-proxy limitation.
Its first-per-day rate is 48/77 (62.3%); spaced is 54/86 (62.8%). These higher
percentages do not make it automatically preferable to the simpler six-sector
rule: it has more measurement requirements and fewer opportunities.

A thrust+B07 union was not among the prespecified unions, so no such combination
is constructed retrospectively here. B07 is a standalone follow-up candidate.

## Primary N lead: thrust plus guarded eight-sector B09

Eight-sector acceleration is meaningfully different from the six-sector version
in this dataset. Under guarded-100, the six-sector B09 rule is 378/690 (54.8%),
whereas the eight-sector rule is 69/105 (65.7%). Under guarded-50, the eight-sector
rule is 44/66 (66.7%). The latter 66 entries occur on 39 dates, with a large share
in 2024 H1. This is a sparse selection from B09's 5,560 entries; it retains 44 or
69 of the parent's 2,890 winners. Its case rests on adding useful opportunities
to the smaller thrust strategy, not on retaining most B09 opportunities.

| All-entry policy | Winners / N | Hit rate | Distinct dates | Extra winners / entries beyond thrust |
|---|---:|---:|---:|---:|
| Thrust alone | 59/92 | 64.1% | 68 | — |
| Add B09 original acceleration in eight | 182/305 | 59.7% | 158 | 123/213 |
| Add B09 midpoint-recovered acceleration in eight | 200/332 | 60.2% | 165 | 141/240 |
| Add B09 guarded-100 acceleration in eight | 128/197 | 65.0% | 116 | 69/105 |
| Add B09 guarded-50 acceleration in eight | 103/158 | 65.2% | 97 | 44/66 |

Guarded-100 more than doubles thrust's N (+114.1%). Guarded-50 increases N by
71.7%. Neither increases the pooled percentage by even two points. Their practical
promise is an added set of winners with similar observed accuracy. The unguarded
and simple midpoint-recovery versions add more entries but dilute accuracy to
about 60%. That makes quote policy an important part of this candidate, not a
minor implementation detail. It remains possible that the guards select favorable
market/measurement conditions in addition to an IV effect.

| Policy | First qualifying signal per day | Sixty-minute spacing |
|---|---:|---:|
| Thrust alone | 48/68 = 70.6% | 55/81 = 67.9% |
| Add guarded-100 eight-sector B09 | 78/116 = 67.2% | 99/148 = 66.9% |
| Add guarded-50 eight-sector B09 | 68/97 = 70.1% | 87/124 = 70.2% |

Guarded-50 has the more attractive observed repetition sensitivities: similar
first-per-day accuracy with 29 more selected dates, and 43 more spaced executions
with a 2.3-point higher percentage. Guarded-100 supplies more N with lower
first/spaced percentages than thrust. Both remain candidates; selecting the guard
after seeing these cells adds selection risk, even though both were predeclared.

| Half-year | Extra guarded-100 B09 winners / N (dates) | Extra guarded-50 B09 winners / N (dates) |
|---|---:|---:|
| 2024 H1 | 24/34 = 70.6% (18) | 21/30 = 70.0% (14) |
| 2024 H2 | 10/17 = 58.8% (12) | 5/8 = 62.5% (4) |
| 2025 H1 | 9/11 = 81.8% (10) | 3/4 = 75.0% (4) |
| 2025 H2 | 15/27 = 55.6% (18) | 9/15 = 60.0% (11) |
| 2026 H1 | 9/12 = 75.0% (8) | 6/8 = 75.0% (5) |
| 2026 H2 through September 18 | 2/4 = 50.0% (3) | 0/1 = 0.0% (1) |

These added B09 executions do not overlap thrust at the same date/minute. The
2024 H1 result helps distinguish this lead from one driven solely by strong recent
2026 observations. The other half-year samples are still small, and 2025 H2 is
clearly weaker. A single recent loss neither disproves nor validates the rule.

## Secondary N lead: IV-qualified opening-range breakouts

The unions were specified before new outcomes were joined. They add qualified
B06, B09 or B10 immediate entries to thrust, or combine all three sources. Identical
date/minute executions count once. The extra-entry statistics exclude all thrust
identities. The all-entry unions retain every original thrust signal.

| All-entry policy | Winners / N | Hit rate | Additional winners / entries beyond thrust |
|---|---:|---:|---:|
| Thrust alone | 59 / 92 | 64.1% | — |
| Thrust + original-acceleration B10 | 75 / 117 | 64.1% | 16 / 25 |
| Thrust + midpoint-recovered-acceleration B10 | 77 / 120 | 64.2% | 18 / 28 |
| Thrust + guarded-100-acceleration B10 | 69 / 106 | 65.1% | 10 / 14 |
| Thrust + balanced-acceleration B10 | 76 / 121 | 62.8% | 17 / 29 |

The midpoint version increases N by 30.4% while keeping the observed all-entry
percentage roughly unchanged. The guarded version increases N by 15.2% with a
small observed percentage increase. These are different choices from an already
declared inventory; the percentages do not establish an optimal quote policy.
The next comparison must keep these definitions fixed, rather than tune them to
the 14–28 added observations.

| Policy | First qualifying signal per day | Sixty-minute spacing |
|---|---:|---:|
| Thrust alone | 48/68 = 70.6% | 55/81 = 67.9% |
| Add original-acceleration B10 | 61/90 = 67.8% | 69/104 = 66.3% |
| Add midpoint-recovered-acceleration B10 | 63/93 = 67.7% | 71/107 = 66.4% |
| Add guarded-100-acceleration B10 | 56/80 = 70.0% | 64/94 = 68.1% |
| Add balanced-acceleration B10 | 62/94 = 66.0% | 70/108 = 64.8% |

The guarded version's observed spaced percentage is similar to thrust while
adding thirteen selected executions. The broader midpoint version adds more
executions but lowers the first/spaced percentages. Thinning occurs after
qualification and can select a different earlier trade; it is not simply deleting
repeats from an unchanged set of chosen thrust trades.

| Half-year | Thrust alone | Thrust + midpoint-acceleration B10 | Thrust + guarded-100-acceleration B10 |
|---|---:|---:|---:|
| 2024 H1 | 9/15 = 60.0% | 14/24 = 58.3% | 11/20 = 55.0% |
| 2024 H2 | 12/19 = 63.2% | 13/22 = 59.1% | 12/19 = 63.2% |
| 2025 H1 | 14/24 = 58.3% | 18/31 = 58.1% | 17/28 = 60.7% |
| 2025 H2 | 7/13 = 53.8% | 11/17 = 64.7% | 10/16 = 62.5% |
| 2026 H1 | 13/16 = 81.2% | 16/20 = 80.0% | 15/18 = 83.3% |
| 2026 H2 through September 18 | 4/5 = 80.0% | 5/6 = 83.3% | 4/5 = 80.0% |

The additions are not consistently better in 2024. Recent high percentages rest
on small samples. Detailed tables provide distinct-date counts and pooled
whole-date intervals; the six halves are not six equally sized independent trials.

## Other surface ideas did not supply a convincing B06 repair

The complete diagnostic registry was retained, including ATM direction, ±25-delta
put richness, call richness, risk reversal, and rising/falling acceleration or
slowing phases. Among B06 diagnostic cells with at least 100 entries, the highest
observed rate is the already counted eight-sector ATM acceleration rule: 74/140,
or 52.9%. The shape coordinates do not provide a stronger large-N B06 result in
this inventory. This is a descriptive scan of reported cells, not a new N cutoff
for a trading rule or an independent confirmation of ATM acceleration.

Requiring the entire propagated bid/ask uncertainty envelope to confirm broad
decline or acceleration produces **zero qualifying entries** in all thirteen
families. That stringent measurement rule cannot currently serve as a useful
entry filter. The result does not mean every midpoint-IV movement is meaningless;
it means this particular conservative envelope test never clears the declared
six/eight-sector threshold.

## Confidence, excluded entries and delayed confirmation

The B09 guarded-100 eight-sector qualifier has a 95% whole-date interval of
54.0–75.9%; guarded-50 has 51.5–78.9%. Their differences from all B09 entries
are +2.6 to +23.7 points and approximately +0.03 to +26.9 points, respectively.
These unadjusted intervals are encouraging for an exploratory transfer, but
they are wide and come from an inventory with many attempted comparisons.

The N-expanding unions have 95% rate intervals of 57.7–71.8% (guarded-100) and
57.2–72.5% (guarded-50). These are intervals for the union's own percentage,
**not a test establishing superiority or noninferiority to thrust**. The evidence
supports investigating more opportunities at similar observed accuracy, rather
than claiming that the union is reliably more accurate.

| B09 eight-sector rule | Qualified | Definite no | Unknown | Entire measurable cohort |
|---|---:|---:|---:|---:|
| Guarded-100 | 69/105 = 65.7% | 2,040/3,983 = 51.2% | 781/1,472 = 53.1% | 2,109/4,088 = 51.6% |
| Guarded-50 | 44/66 = 66.7% | 1,367/2,758 = 49.6% | 1,479/2,736 = 54.1% | 1,411/2,824 = 50.0% |

Unknown entries include many winners. Neither candidate turns them into failures
or assumes that rejecting them is costless. The full audit separately labels
**741 primary recipe entries before 10:05**, whose full reference would start
before the session. This is structural missingness, not a failed download. Those
741 include 350 B01, 167 B09 and 120 B10 immediate entries, plus smaller counts
in other families. B06 has no such early entries in this frozen population.
Other unresolved observations retain explicit quote/expiry or issuer-quality
reasons. Family counts overlap and are not a count of unique executable trades.

At a genuinely new T+15 entry, all admitted B06 parents achieve 1,201/2,381
(50.4%). Requiring same-sector price-rise/IV-decline confirmation both before
the original signal and during the subsequent fifteen minutes produces 83/156
(53.2%), versus 287/584 (49.1%) for pre-confirmed but definite post-nonqualifiers.
Sixty-one post-unknowns produce 29 winners. This is a modest small-pool hint, with
a different entry price and a new full hour. It cannot be used to relabel the
original B06 entry; one parent fails the fresh VT admission.

For completeness, the surface-direction diagnostic scan contains isolated
other-family cells such as B01 full-window rising ATM IV in eight sectors
(82/133 = 61.7%) and B05 full-window rising call richness in eight
(64/106 = 60.4%). These are recorded in the full inventory, not selected as new
production rules from a post-hoc ranking. They do not corroborate the original
falling-IV B06 thesis.

## Interpretation limits and evidence map

The register contains 105 distinct rules: 104 evaluated at the original entry
and one post-entry rule used only for a new T+15 entry. It includes 22 primary
falling/acceleration or paired-price rules, ten weighted rules, 64 surface-direction
diagnostics, four quote-envelope diagnostics, two price controls, two contemporaneous
confirmation rules, and the delayed rule. The direction/shape coordinates are
related; they are not 105 independent confirmations of an effect.

All thirteen frozen price families are retained, including weak cells. A filter
cannot increase N relative to its own parent. The N-expansion comparison explicitly
uses thrust as the smaller baseline and adds entries from other families. No new
entry generator, fitted cutoff, calendar exclusion or adverse barrier was selected
after viewing these results.

The score and native price inputs are unchanged. Every admitted primary entry
requires all earlier RTH minute lows and its entry open to exceed that day's VT.
This is a causal through-entry requirement. Future session lows do not determine
admission. Same-minute double touches are ambiguous; ambiguities and neither-touch
outcomes stay in N. All primary analyses exclude the ten development dates.

Whole-date resampling, including zero-entry selected dates, uses 5,000 draws and
seed 20260919. It accounts for within-date dependence more honestly than treating
every overlapping signal as a separate independent trial. It does not remove
regime shifts, serial dependence or selection across many attempted ideas. These
are exploratory intervals without a multiple-comparison adjustment. No untouched
holdout is claimed. Tiny perfect samples do not receive certainty-looking intervals.

The original 150-day sector/policy calculations reproduce exactly across 45,760
observations, with zero numerical differences. This rules out a changed version
of those IV measurements as the explanation for the larger-sample result. It does
not by itself prove the original theory: expanding the dates and evaluating the
user's current +5/−10 criterion changes the evidence. Early pilot percentages,
different price gates and different adverse barriers are not interchangeable.

## Verification and independent review

All **97,656 comparison rows**, **1,848 opportunity-union rows**, and **312 original
unfiltered baseline rows** reconcile independently. Every native source hash and
dated expiry selection was checked. The 1,000-event feature sample checks all five
quote policies, four surface descriptors, endpoint and price changes, quote ranges,
breakout slopes and post-entry values: **68,000 scalar checks**, with maximum
numerical error about 5.44e−15. The original 45,760-measurement replay remains exact.
Twenty-three scoped tests and Ruff pass, including interrupted-registry recovery.

The final requested Claude Opus 5/xhigh code review returned **CONDITIONAL PASS**
over sixteen implementation files. Its medium findings concerned zero-qualifier
diagnostics, structural missingness, informative missingness in the presentation,
and a non-atomic registration writer. The first three now have explicit output
tables and disclosures. A separately tested safe registration writer supersedes
the original and writes the completion inventory last. No scored outcome or
trading-rule threshold changed in response to that review.

The remaining artifact/provenance points are documented in REVIEW_RESOLUTION.md:
3,524 canonical matching IDs are unique; fifty older validated issuer bodies have
no recorded HTTP status and are labeled accordingly; all 421 issuer as-of dates
are strictly earlier than their study dates; no current freeze contains conflicting
input/output hash expectations. The review verdict is reported as conditional,
not relabeled PASS after local follow-up checks. The new reporting/registration
helpers received local checks, not a separate claim of another Claude review.

- [Complete tables, including missingness disclosures](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/RESULT_TABLES.md).
- [Every idea and its treatment](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/IDEA_INVENTORY.md).
- [Review findings and dispositions](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/REVIEW_RESOLUTION.md).
- [Reproduction instructions](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/REPRODUCTION.md).
- [Native, arithmetic and count verification](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1/independent_verification.json).
- [Additional missingness and provenance audit](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1/additive_review_audit.json).
- [All day/sector coverage](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1/coverage_sector_days.csv).

![Observed accuracy and opportunity counts across the fixed inventory](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1/accuracy_vs_n.png)
