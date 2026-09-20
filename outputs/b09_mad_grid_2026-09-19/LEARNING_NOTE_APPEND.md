

### 11.31 — September 20: B09 sector MAD grid, both direction definitions

**Completed result, not a new validated strategy.** The user froze a 4×6 grid:
scaled-MAD cutoffs 1, 2, 3, 4 exceeded in at least 4–9 of the eleven sector ETFs.
They then explicitly requested both downward acceleration alone and downward
acceleration while IV is already falling: 48 cells. No lower cutoffs, smaller
breadth, new entry recipes or post-target penalties were added after outcomes.

**Population and comparability.** Existing exact MAD coverage supports January 2,
2025–September 18, 2026, with sixty prior-session warmup. It does not supply a
full-2024 MAD outcome test. The parent is 3,141 B09 signals on 178 active dates
within 239 selected research dates; ten development dates remain excluded. Plain
B09 scores 1,704/3,141 = 54.25%. Do not compare new filtered percentages against
the 2,890/5,560 = 51.98% baseline from the larger 2024–2026 population.

Every entry retains the strict causal above-VT rule: all earlier same-session
native minute lows and the entry open exceed same-date VT. Future session prices
do not determine eligibility. Success remains +5 before −10 within sixty native
minute bars including entry; neither and ambiguous outcomes stay in the denominator.
A later giveback after +5 does not undo a win. No option-profitability inference.

**Exact IV definition.** At entry T, read the existing window ending T−1, covering
T−30…T−1. This explicitly differs from the older B06 reference ending T−6. Fit
the inherited actual-time IV slopes b1/b2 within the two fifteen-minute halves;
a=(b2−b1)/15. M=−a/(1.4826×historical MAD). The historical ruler uses sixty
strictly prior sessions, the same ETF/hour block, both acceleration signs, all
regimes and equal total weight per date. This is zero-centered scaled magnitude,
not a median-centered z-score, percentile, probability or quote-resolved signal.

The signed rule requires M>k. The falling rule also requires b2<−1e−12 in the
same qualifying ETF. Thus IV rising more slowly can qualify for signed, while
the falling rule demands an actual downward trend in the latest fifteen minutes.
It does not demand that every individual minute decline. A sector must meet both
conditions itself; votes from different sectors cannot satisfy separate legs.
The cutoff is strictly exceeded; the sector-count condition is inclusive.

**Learning 1 — four sectors at M>1 is the useful N region in the requested grid.**

| Rule | Winners / N | Hit rate | Active dates | Entry retention |
|---|---:|---:|---:|---:|
| Plain B09 | 1,704 / 3,141 | 54.25% | 178 | 100% |
| M>1, ≥4, acceleration alone | 139 / 235 | 59.15% | 100 | 7.5% |
| M>1, ≥4, IV also falling | 115 / 188 | 61.17% | 95 | 6.0% |
| M>1, ≥5, acceleration alone | 53 / 80 | 66.25% | 54 | 2.5% |
| M>1, ≥5, IV also falling | 43 / 64 | 67.19% | 45 | 2.0% |

The predeclared high-N selection first required observed uplift versus plain B09
in each completed half, then ranked retained completed-half N. Signed 1/four
wins that ordering, with 225 completed-half signals. Falling 1/four is a separate
accuracy/N compromise with 181. This ranking is not a significance test or evidence
that 1/four is the globally optimal rule. Both discard most parent opportunities.

At 1/four, relaxing the falling requirement adds 47 signals and 24 winners (51.06%).
Forty are definite falling-rule nonqualifiers, 20/40; seven have an unknown falling
classification, 4/7. Do not relabel all 47 as definitely rising-IV events. Falling
1/four retains only 115 of the parent's 1,704 winners; 1,589 successes are excluded.

**Learning 2 — improvement repeats across completed halves, not every observed period.**

| Rule | 2025 H1 | 2025 H2 | 2026 H1 | Partial 2026 H2 |
|---|---:|---:|---:|---:|
| Plain B09 | 496/897 = 55.30% | 587/1,215 = 48.31% | 514/858 = 59.91% | 107/171 = 62.57% |
| Signed 1/four | 45/78 = 57.69% | 51/89 = 57.30% | 38/58 = 65.52% | 5/10 = 50.00% |
| Falling 1/four | 37/61 = 60.66% | 39/69 = 56.52% | 35/51 = 68.63% | 4/7 = 57.14% |
| Signed 1/five | 18/31 = 58.06% | 18/28 = 64.29% | 15/19 = 78.95% | 2/2 = 100% |
| Falling 1/five | 16/25 = 64.00% | 15/23 = 65.22% | 11/15 = 73.33% | 1/1 = 100% |

Only the three completed halves drive stability ranking. The partial half stops
September 18 and is not an untouched holdout. Its four-sector results are worse
than its plain parent; its five-sector 100% observations contain only one/two
signals. Neither sparse observation establishes success or failure by itself.

**Learning 3 — the four-sector advantage is not solely repeated neighboring signals.**
First qualifying signal/day and greedy sixty-minute spacing are timestamp-only,
reset daily, and occur after applying each filter. Compare like execution policies:

| Rule | First/day | Sixty-minute spacing |
|---|---:|---:|
| Plain B09 | 97/178 = 54.49% | 285/554 = 51.44% |
| Signed 1/four | 60/100 = 60.00% | 84/142 = 59.15% |
| Falling 1/four | 61/95 = 64.21% | 76/121 = 62.81% |
| Signed 1/five | 34/54 = 62.96% | 40/60 = 66.67% |
| Falling 1/five | 28/45 = 62.22% | 33/50 = 66.00% |

Both four-sector rules retain positive observed uplift in each completed half
under all three execution policies. Signed 1/five fails that test in first/day
2025 H1. Filtered first/day events may occur later than plain first/day events;
these are different executable policies, not paired identical-entry causal effects.

**Learning 4 — stronger magnitude or breadth mostly destroys N.** Across cutoffs
2–4, the largest pooled N is 26. At cutoff one, requiring six sectors leaves only
25 signed or 22 falling entries; seven–nine sectors are sparser. The four favorable
raw cells are adjacent at the least restrictive boundaries. There is no broad
robust plateau, and no authorized sub-one/fewer-than-four sweep was performed.

**Learning 5 — unknown coverage is not evidence against an entry.** The eleven
ETFs stay fixed, including XLRE. Qualify when enough observed sectors pass; reject
only when passing plus unknown sectors cannot reach the required count; otherwise
unknown. No forward fill, denominator reduction or missing-as-negative vote.
Signed 1/four has 212 unknown entries, 130 winners (61.32%); falling 1/four has
183, 111 winners (60.66%). Their measurable parent rates are 53.74% and 53.85%.
Missing-sector exclusions are an opportunity cost and cannot be used to claim
the excluded group consists of failures. Scores were usable in all eleven ETFs
at 1,788 entries; remaining entries had six–ten available sectors. No new fetch.

**Learning 6 — the apparent uplift remains uncertain after search.** Five thousand
whole-date draws include zero-event dates and use shared draws for each parent
comparison. Signed 1/four pooled uplift interval is −1.55 to +11.35 percentage
points; falling 1/four is +0.01 to +13.63. These are unadjusted for the 48-cell
search, earlier research and serial dependence. A lower endpoint of +0.01 is not
decisive evidence. Three completed half-years cannot establish regime invariance.

For context, the older guarded-100 eight-sector B09 acceleration rule has 35/54
=64.81% over the SAME 2025–2026 dates. Falling MAD 1/four offers 188 versus 54
signals (3.5×), at 61.17% versus 64.81%. The new calculation changes timing,
normalization, breadth and measurement policy; its differences cannot be credited
to MAD alone. The old 69/105 headline includes 2024 and is not the correct comparator.

**Verification and review.** All 66 source-file hashes and the original price-score
hash verified. Memberships were frozen without outcome columns. Ten tests and
Ruff pass; a separate local scalar implementation replays 150,768 classifications,
all 3,474 summary rows and twelve inherited half-year/execution baselines. Threshold,
breadth and falling-subset nesting hold. These checks were performed by the same
assistant. Independent Claude code review remains NOT RUN under the side-thread
prohibition on separate reviewers; no PASS or conditional sign-off is implied.

The next work is a proposal only: transfer fixed candidate RULES to all eligible
events of a small, declared price-parent set; never select historical winning
events for the test. Index-IV normalization remains untested. Preserve every
cell and tradeoff instead of retrospectively selecting a single winner as proven.

- [Full findings](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/FINDINGS.md).
- [All 48 half-year cells](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/ALL_48_RESULTS.md).
- [Frozen protocol](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/PROTOCOL.md).
- Central evidence: `/Users/dgrissen/Dev/central_trade_data/thetadata/b09_mad_grid_2026-09-19-v1/`.
