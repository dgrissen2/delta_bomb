# Combined B09, B05 and B07 opportunity expansion

September 20, 2026. **Combining all three expansions gives 427 winners / 685
distinct signals = 62.3%, versus 198/318 = 62.3% for the original B09 OR rule.**
That adds 367 entries and 229 winners, with 62.4% accuracy among the additions.
The no-spacing historical result supports substantially more opportunities at a
similar observed rate; it does not prove future accuracy is preserved.

## Exactly what was combined

At each entry minute accept B09 with sector F4 OR SPX confirmation, OR existing
B05 with F4, OR B09 with the fixed five-endpoint IV persistence rule, OR original
B07 with six-sector acceleration. The persistence route already includes baseline
B09 OR. Deduplicate by Eastern date/minute while retaining every qualifying route.

This combines accepted entry sets. It does not require B05, B09 and B07 to agree;
it does not apply the relaxed IV timing to B05/B07; it does not add volume or skew.
Each constituent keeps its existing definition, including B07's older measurement
clock. There is no new threshold sweep or selection of an optimal subset.

Same 239 selected research dates, January 2025–September 18, 2026; strict causal
above-VT at entry, +5 before -10 within 60 native minute bars including entry.
This is not the full exchange calendar. All non-target outcomes remain in N.
Above-VT uses all observed session lows before entry and entry open, not future
session prices. Later post-target reversals do not change a winner.

## Primary result: no spacing

| Cohort | Winners / signals | Accuracy | 95% whole-date interval | Active dates |
|---|---:|---:|---:|---:|
| Original B09 F4 OR SPX | 198/318 | 62.3% | 55.6–68.4% | 121 |
| All three expansions combined | 427/685 | 62.3% | 57.5–66.8% | 163 |
| Genuinely added entries only | 229/367 | 62.4% | 56.8–67.9% | 153 |

The combined count rises 115.4%, with 42 additional active dates. Median signals
per research date rise from 1 to 2; per active date, from 2 to 3. Added-only active
dates include 111 dates already active under baseline and 42 entirely new dates.

Combined-minus-baseline accuracy is +0.07 percentage points, with a paired 95%
whole-date interval of -3.82 to +4.04 points. This does not establish noninferiority.
The pooled union's narrower interval reflects these historical observations under
the resampling assumptions, not independent new data or a correction for selection.

Outcome mix: baseline 198 target / 77 adverse / 43 neither; combined 427 target /
166 adverse / 92 neither; additions 229 target / 89 adverse / 49 neither. None of
these selected executions is ambiguous. We retain the user's +5-first objective.

## Where the duplicates were

Separate experiments supplied 105 B05 additions, 174 persistence additions and
90 B07 additions: 369 memberships, but **367 distinct new timestamps**.

| Mutually exclusive source among additions | Winners / signals | Accuracy |
|---|---:|---:|
| B05 only | 63/104 | 60.6% |
| B09 persistence only | 110/173 | 63.6% |
| B07 only | 55/88 | 62.5% |
| B05 and B07 together | 1/1 | 100% |
| B09 persistence and B07 together | 0/1 | 0% |
| Total distinct additions | 229/367 | 62.4% |

One shared addition was a winner; the other reached neither barrier. Thus sum of
separate added winners 64+110+56=230 loses one duplicate winner, leaving 229.
Baseline plus additions is 318+367=685 and 198+229=427. The single-observation
overlap cells are accounting details, not evidence for an agreement filter.

## Every half-year

| Half-year | Baseline winners/N | Baseline rate | Combined winners/N | Combined rate | Combined 95% interval | Added winners/N |
|---|---:|---:|---:|---:|---:|---:|
| 2025 H1 | 58/96 | 60.4% | 127/205 | 62.0% | 53.7–69.5% | 69/109 |
| 2025 H2 | 78/130 | 60.0% | 159/268 | 59.3% | 51.3–66.9% | 81/138 |
| 2026 H1 | 50/74 | 67.6% | 115/173 | 66.5% | 57.7–74.1% | 65/99 |
| 2026 H2 through September 18 | 12/18 | 66.7% | 26/39 | 66.7% | 41.9–85.4% | 14/21 |

No-spacing combined rates stay near the baseline in each half, with more signals.
The partial final half still has only 12 active dates and should not establish
stability. Complete per-half intervals, differences, outcomes, medians and research
date denominators are in ALL_RESULTS.md and the central summary.csv.

## Chronological spacing changes the tradeoff

| Policy | Baseline winners/N | Baseline accuracy | Combined winners/N | Combined accuracy |
|---|---:|---:|---:|---:|
| All entries | 198/318 | 62.3% | 427/685 | 62.3% |
| First qualifying entry each day | 70/121 | 57.9% | 95/163 | 58.3% |
| At least 60 minutes since last accepted entry | 107/175 | 61.1% | 191/327 | 58.4% |

The full union is thinned chronologically with a daily reset. Under 60-minute
spacing, 184 executions/108 winners are newly selected relative to the spaced
baseline, while 32 baseline executions/24 winners are displaced: net +152 entries
and +84 winners. Newly selected executions can include baseline-qualified entries
that the old spacing policy skipped, so these are policy changes, not the raw
367 additions. First/day similarly adds 76/45 and displaces 34/20, net +42/+25.

The spaced accuracy difference is -2.73 points, with paired date interval -8.48
to +3.23 points. Combined spaced rates by half are 60.9%, 52.5%, 65.6%, and 50.0%.
2025 H2 is the weakest completed half; do not hide it behind the pooled count.
No spacing remains the declared primary comparison; neither policy was optimized.

## Are these new market conditions or more entries on similar days?

Of the 367 additions, 279 occur on dates with a baseline entry and hit 189/279 =
67.7%. The other 88 occur on 42 entirely new dates and hit 40/88 = 45.5%.
The new dates' half-year results are 12/23, 10/30, 11/24 and 7/11.

This means the strong pooled expansion is concentrated on already-active dates.
It does not mean a live rule can simply discard the weaker group: a baseline
signal may occur later that day. This is a retrospective diagnostic, never a
causal admission gate, and these subgroup rates remain uncertain.

Removing each research date separately leaves the combined pooled rate at
61.8–62.8%; the top five winning dates contribute 49/427 = 11.5% of winners,
and the largest contributes 13. The baseline deletion range is 61.3–63.1%.
These are sensitivity ranges, not confidence intervals or independent trials.

## Confidence and verification

Five thousand paired whole-date bootstrap draws per period, seed 20260920, include
research dates with zero entries and preserve within-date clustering. They do not
adjust for earlier 105-rule/48-cell searches, selection of these components after
seeing their outcomes, or dependence across dates. This additional union test is
exploratory. No new IV-versus-price matching, volume test or skew measurement ran.

Four boundary tests pass, covering cross-parent duplicates, retention of baseline
membership, conflicting outcomes and missing outcomes. Ruff passes. A separate
local verification implementation reconstructs all 685 memberships, replays all
685 native SPX entry/VT/first-touch paths with complete minutes, verifies all 239
native source hashes, checks 35 summary rows, 15 policy changes, 19 route-pattern
rows, 10 date-novelty rows and 956 day deletions, and independently reproduces the
pooled paired bootstrap. All 60 prior component summary cells reconcile exactly.

The prior Claude review concerned the proposal; this new union has local checks,
not a new independent reviewer approval. Original research and concurrent files
are unchanged. No market-data calls, option-profitability claims or dashboard edits.

Data and exact per-entry route labels:
`/Users/dgrissen/Dev/central_trade_data/thetadata/b09_combined_expansion_2026-09-20-v1`.
